import requests
import re

class TallyVoucherUpdater:
    def __init__(self, tally_url="http://localhost:9000"):
        self.tally_url = tally_url

    def build_voucher_guid(self, from_ledger, to_ledger, amount, voucher_type, date):
        return f"{from_ledger}_{to_ledger}_{amount}_{voucher_type}_{date}"

    def validate_voucher_data(self, data: dict, required_fields: list):
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        if "amount" in data:
            try:
                float(data["amount"])
            except ValueError:
                raise ValueError("Amount must be numeric")

        if "date" in data and not re.match(r"^\d{8}$", str(data["date"])):
            raise ValueError(f"Date {data['date']} must be in YYYYMMDD format")
        return True

    def build_delete_xml(self, company_name, remote_id, voucher_type):
        return f"""
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
                </STATICVARIABLES>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER REMOTEID="{remote_id}" VCHTYPE="{voucher_type}" ACTION="Delete" OBJVIEW="Accounting Voucher View">
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>
""".strip()

    def build_create_xml(self, data: dict):
        narration = data.get("narration") or f"Transfer from {data['from_ledger']} to {data['to_ledger']}"
        new_remote_id = self.build_voucher_guid(
            data["from_ledger"], data["to_ledger"], data["amount"], data["voucher_type"], data["date"]
        )

        return f"""
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>{data['company_name']}</SVCURRENTCOMPANY>
                </STATICVARIABLES> 
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER REMOTEID="{new_remote_id}" VCHTYPE="{data['voucher_type']}" ACTION="Create" OBJVIEW="Accounting Voucher View">
                        <DATE>{data['date']}</DATE> 
                        <EFFECTIVEDATE>{data['date']}</EFFECTIVEDATE>
                        <VOUCHERTYPENAME>{data['voucher_type']}</VOUCHERTYPENAME>
                        <PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>
                        <NARRATION>{narration}</NARRATION>
                        <PARTYLEDGERNAME>{data['from_ledger']}</PARTYLEDGERNAME>

                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{data['from_ledger']}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{data['amount']}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>

                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{data['to_ledger']}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{data['amount']}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>
""".strip()

    def post_to_tally(self, xml_string):
        headers = {"Content-Type": "application/xml"}
        try:
            response = requests.post(
                self.tally_url,
                data=xml_string.encode("utf-8"),
                headers=headers,
                timeout=10
            )
            return response
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to communicate with Tally server: {e}")

    def update_voucher(self, old_data: dict, new_data: dict):
        """Update voucher transactionally: delete old, create new, restore if needed."""
        # Validate both old and new data
        self.validate_voucher_data(old_data, ["company_name", "from_ledger", "to_ledger", "amount", "voucher_type", "date"])
        self.validate_voucher_data(new_data, ["company_name", "from_ledger", "to_ledger", "amount", "voucher_type", "date"])

        # Step 1: Delete old voucher
        old_remote_id = self.build_voucher_guid(
            old_data["from_ledger"], old_data["to_ledger"], old_data["amount"], old_data["voucher_type"], old_data["date"]
        )
        delete_xml = self.build_delete_xml(old_data["company_name"], old_remote_id, old_data["voucher_type"])
        print(f"Deleting voucher with Remote ID: {old_remote_id}")
        delete_response = self.post_to_tally(delete_xml)

        # Check delete result
        if not delete_response or delete_response.status_code != 200:
            raise RuntimeError("Failed to connect to Tally during deletion.")

        if "<DELETED>0</DELETED>" in delete_response.text:
            raise RuntimeError("Voucher not found or could not be deleted. Aborting update.")

        print("Old voucher deleted successfully.")

        # Step 2: Create new voucher
        print(f"Creating new voucher for {new_data['amount']}")
        create_xml = self.build_create_xml(new_data)
        create_response = self.post_to_tally(create_xml)
        
        if not create_response:
            print("Failed to connect to Tally during creation. Restoring old voucher...")
            restore_xml = self.build_create_xml(old_data)
            self.post_to_tally(restore_xml)
            raise RuntimeError("Failed to create updated voucher. Old voucher restored.")

        if "<CREATED>0</CREATED>" in create_response.text:
            print("Failed to create updated voucher. Restoring old voucher...")
            restore_xml = self.build_create_xml(old_data)
            self.post_to_tally(restore_xml)
            raise RuntimeError("Updated voucher creation failed. Old voucher restored.")

        print("Voucher updated successfully.")

        return {
            "response": 
                "Voucher updated successfully"
        }