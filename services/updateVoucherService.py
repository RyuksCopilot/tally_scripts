import requests
import re
import xml.etree.ElementTree as ET

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
        narration = data["narration"] or f"Transfer from {data['from_ledger']} to {data['to_ledger']}"
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

   
    def fetch_vouchers(self, company_name):
        """Fetch all vouchers from Tally for a given company."""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <TALLYREQUEST>Export Data</TALLYREQUEST>
            </HEADER>
            <BODY>
                <EXPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>Voucher Register</REPORTNAME>
                        <STATICVARIABLES>
                            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            <SVCurrentCompany>{company_name}</SVCurrentCompany>
                        </STATICVARIABLES>
                    </REQUESTDESC>
                </EXPORTDATA>
            </BODY>
        </ENVELOPE>
        """
        response = requests.post(self.tally_url, data=xml_request.encode("utf-8"))
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch vouchers: {response.status_code}")
        return ET.fromstring(response.text)

    def find_remote_id(self, company_name, search_criteria: dict):
        """
        Find RemoteID of a voucher by matching info.
        search_criteria example:
        {
            "voucher_type": "Contra",
            "voucher_number": "1",
            "date": "20250401",
            "from_ledger": "Kunal",
            "to_ledger": "SBI",
            "amount": "70000"
        }
        """
        root = self.fetch_vouchers(company_name)
        
        

        matched = []
        
        for voucher in root.findall(".//VOUCHER"):
            # Extract basic voucher info
            vch_type = voucher.get("VCHTYPE", "")
            vch_number = voucher.findtext("VOUCHERNUMBER", "")
            vch_date = voucher.findtext("DATE", "")
            
            # --- Step 1: Basic filters ---
            if "voucher_type" in search_criteria and search_criteria["voucher_type"] != vch_type and  search_criteria["voucher_type"] != None:
                continue
            if "voucher_number" in search_criteria and search_criteria["voucher_number"] != vch_number and search_criteria["voucher_number"] != None:
                continue
            if "date" in search_criteria and search_criteria["date"] != vch_date and search_criteria["date"] != None:
                continue
    
            # --- Step 2: Ledger filters ---
            ledgers = []
            for ledger_entry in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
                name = ledger_entry.findtext("LEDGERNAME", "")
                amount = ledger_entry.findtext("AMOUNT", "")
                print(name,amount,search_criteria)
                ledgers.append((name, amount))
            
            # Separate debit/credit (negative = from_ledger, positive = to_ledger)
            from_ledger = next((l for l, amt in ledgers if amt.startswith("-")), None)
            to_ledger = next((l for l, amt in ledgers if not amt.startswith("-")), None)
            abs_amount = next((amt.replace("-", "") for _, amt in ledgers if amt), None)
        
            if "from_ledger" in search_criteria and search_criteria["from_ledger"] != from_ledger and search_criteria["from_ledger"] != None:
                continue
            if "to_ledger" in search_criteria and search_criteria["to_ledger"] != to_ledger and search_criteria["to_ledger"] != None:
                continue
            if "amount" in search_criteria and search_criteria["amount"] != None:
                criteria_amount = round(float(search_criteria["amount"]), 2)
                voucher_amount = round(float(abs_amount), 2)

                if criteria_amount != voucher_amount:
                    continue

            matched.append({
            "remote_id": voucher.get("REMOTEID"),
            "company_name": company_name,
            "voucher_type": vch_type,
            "voucher_number": vch_number,
            "date": vch_date,
            "from_ledger": from_ledger,
            "to_ledger": to_ledger,
            "amount": abs_amount,
            "narration": voucher.findtext("NARRATION", "")
            })
            
        print(len(matched),matched)
        
        if len(matched) > 1:
            raise ValueError("More than one voucher matched the given criteria.")
        elif len(matched) < 1:
            raise ValueError("No voucher found matching the given criteria.")    
        
        return matched[0]

        

   
    
    def fetch_voucher_by_remote_id(self, remote_id: str, company_name: str):
        xml_payload = f"""
        <ENVELOPE>
          <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
          </HEADER>
          <BODY>
            <EXPORTDATA>
              <REQUESTDESC>
                <REPORTNAME>Voucher</REPORTNAME>
                <STATICVARIABLES>
                  <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                  <SVCompany>{company_name}</SVCompany>
                  <SVVCHID>{remote_id}</SVVCHID>
                </STATICVARIABLES>
              </REQUESTDESC>
            </EXPORTDATA>
          </BODY>
        </ENVELOPE>
        """
        response = requests.post(self.tally_url, data=xml_payload)
        response.raise_for_status()
        return response.text
    
    def update_voucher(self, old_lookup: dict, new_data: dict):
        """
        Update voucher transactionally: delete old, create new, restore if needed.
        """

        # Validate only the new data
        self.validate_voucher_data(new_data, ["company_name", "from_ledger", "to_ledger", "amount", "voucher_type", "date"])

        # Step 1: Resolve RemoteID and fetch full old voucher details
        old_voucher_full = self.find_remote_id(old_lookup["company_name"], old_lookup)
        
        if not old_voucher_full:
            raise RuntimeError("Could not resolve old voucher. Aborting update.")

        remote_id = old_voucher_full["remote_id"]
        
        if not remote_id:
            raise RuntimeError("Could not resolve RemoteID for old voucher. Aborting update.")


        # Step 2: Delete old voucher
        delete_xml = self.build_delete_xml(old_lookup["company_name"], remote_id, old_lookup["voucher_type"])
        delete_response = self.post_to_tally(delete_xml)

        if not delete_response or delete_response.status_code != 200:
            raise RuntimeError("Failed to connect to Tally during deletion.")

        if "<DELETED>0</DELETED>" in delete_response.text:
            raise RuntimeError("Voucher not found or could not be deleted. Aborting update.")


        # Step 3: Create new voucher
        create_xml = self.build_create_xml(new_data)
        create_response = self.post_to_tally(create_xml)

        if not create_response or create_response.status_code != 200:
            restore_xml = self.build_create_xml(old_voucher_full)  #  use original full voucher
            self.post_to_tally(restore_xml)
            raise RuntimeError("Failed to create updated voucher. Old voucher restored.")

        if "<CREATED>0</CREATED>" in create_response.text:
            restore_xml = self.build_create_xml(old_voucher_full)  #  use original full voucher
            self.post_to_tally(restore_xml)
            raise RuntimeError("Updated voucher creation failed. Old voucher restored.")

        return {"response": "Voucher updated successfully"}
   
    def delete_voucher(self, old_lookup: dict):
        """
        Update voucher transactionally: delete old, create new, restore if needed.
        """

        # Step 1: Resolve RemoteID and fetch full old voucher details
        old_voucher_full = self.find_remote_id(old_lookup["company_name"], old_lookup)
        
        if not old_voucher_full:
            raise RuntimeError("Could not resolve old voucher. Aborting update.")

        remote_id = old_voucher_full["remote_id"]
        
        if not remote_id:
            raise RuntimeError("Could not resolve RemoteID for old voucher. Aborting update.")


        # Step 2: Delete old voucher
        delete_xml = self.build_delete_xml(old_lookup["company_name"], remote_id, old_lookup["voucher_type"])
        delete_response = self.post_to_tally(delete_xml)

        if not delete_response or delete_response.status_code != 200:
            raise RuntimeError("Failed to connect to Tally during deletion.")

        if "<DELETED>0</DELETED>" in delete_response.text:
            raise RuntimeError("Voucher not found or could not be deleted. Aborting update.")

        return {"response": "Voucher deleted successfully"}
