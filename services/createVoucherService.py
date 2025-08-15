import requests
import re

class TallyVoucherManager:
    def __init__(self, tally_url="http://localhost:9000"):
        self.tally_url = tally_url
        self.required_fields = [
            "company_name", "from_ledger", "to_ledger",
            "amount", "voucher_type", "date"
        ]
        self.all_fields = self.required_fields + ["narration", "voucher_guid"]

    def validate_input(self, data: dict):
        for field in self.required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        try:
            float(data["amount"])
        except ValueError:
            raise ValueError("Amount must be numeric")

        if not re.match(r"^\d{8}$", str(data["date"])):
            raise ValueError("Date must be in YYYYMMDD format")

        return True

    def build_voucher_guid(self, from_ledger, to_ledger, amount, voucher_type, date):
        return f"{from_ledger}_{to_ledger}_{amount}_{voucher_type}_{date}"

    def build_xml(self, data: dict, action="Create"):
        voucher_guid = data.get("voucher_guid") or self.build_voucher_guid(
            data["from_ledger"], data["to_ledger"],
            data["amount"], data["voucher_type"], data["date"]
        )

        narration = data.get("narration") or f"Transfer from {data['from_ledger']} to {data['to_ledger']}"

        xml = f"""
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
                    <VOUCHER REMOTEID="{voucher_guid}" 
                             VCHTYPE="{data['voucher_type']}" ACTION="{action.capitalize()}"
                             OBJVIEW="Accounting Voucher View">
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
"""
        return xml.strip()

    def post_to_tally(self, xml_string):
        headers = {"Content-Type": "application/xml"}
        try:
            response = requests.post(
                self.tally_url,
                data=xml_string.encode("utf-8"),
                headers=headers,
                timeout=10
            )
            return {"status": response.status_code, "response": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def save_voucher(self, data: dict, action="Create"):
        self.validate_input(data)
        xml_payload = self.build_xml(data, action=action)
        return self.post_to_tally(xml_payload)