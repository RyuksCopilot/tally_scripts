import requests
import re
import uuid
from datetime import datetime


class TallyInventoryManagement:
    def __init__(self, tally_url="http://localhost:9000"):
        self.tally_url = tally_url

    # ---------- Utilities ----------
    def to_snake_case(self, value: str) -> str:
        """Convert string to snake_case for GUIDs or identifiers"""
        value = re.sub(r'[\s-]+', '_', value)
        value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
        return value

    def generate_guid(self, item_name: str, date: str) -> str:
        """Generate a unique GUID using item name + date + UUID"""
        item_key = self.to_snake_case(item_name)
        return f"{item_key}_{date}"

    def post_to_tally(self, xml_string: str):
        """Send XML payload to Tally"""
        headers = {"Content-Type": "application/xml"}
        try:
            response = requests.post(
                self.tally_url, data=xml_string.encode("utf-8"), headers=headers, timeout=10
            )
            return {"status": response.status_code, "response": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    # ---------- Stock Item ----------
    def create_stock_item(self, company_name, item_name, parent_group, unit, opening_balance=0):
        """Create a stock item in Tally"""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <TALLYREQUEST>Import Data</TALLYREQUEST>
            </HEADER>
            <BODY>
                <IMPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>All Masters</REPORTNAME>
                        <STATICVARIABLES>
                            <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
                        </STATICVARIABLES>
                    </REQUESTDESC>
                    <REQUESTDATA>
                        <TALLYMESSAGE xmlns:UDF="TallyUDF">
                            <STOCKITEM NAME="{item_name}" ACTION="Create">
                                <NAME.LIST>
                                    <NAME>{item_name}</NAME>
                                </NAME.LIST>
                                <PARENT>{parent_group}</PARENT>
                                <BASEUNITS>{unit}</BASEUNITS>
                                <OPENINGBALANCE>{opening_balance}</OPENINGBALANCE>
                            </STOCKITEM>
                        </TALLYMESSAGE>
                    </REQUESTDATA>
                </IMPORTDATA>
            </BODY>
        </ENVELOPE>
        """
        return self.post_to_tally(xml_request.strip())

    # ---------- Stock Journal ----------
    def create_stock_journal(
        self, company_name, narration, item_name, qty, unit, godown="Main Location", date=None
    ):
        """Create a stock journal entry in Tally with auto-generated GUID"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")  # default = today's date

        voucher_guid = self.generate_guid(item_name, date)

        xml_request = f"""
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
                            <VOUCHER REMOTEID="{voucher_guid}" VCHTYPE="Stock Journal" ACTION="Create">
                                <DATE>{date}</DATE>
                                <VOUCHERTYPENAME>Stock Journal</VOUCHERTYPENAME>
                                <NARRATION>{narration}</NARRATION>

                                <!-- Inward Entry -->
                                <INVENTORYENTRIESIN.LIST>
                                    <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
                                    <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                    <DESTINATIONGODOWN>{godown}</DESTINATIONGODOWN>
                                    <ACTUALQTY>{qty} {unit}</ACTUALQTY>
                                    <BILLEDQTY>{qty} {unit}</BILLEDQTY>
                                </INVENTORYENTRIESIN.LIST>

                                <!-- Outward Entry -->
                                <ALLINVENTORYENTRIES.LIST>
                                    <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
                                    <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                                    <SOURCEDGODOWN>{godown}</SOURCEDGODOWN>
                                    <ACTUALQTY>{qty} {unit}</ACTUALQTY>
                                    <BILLEDQTY>{qty} {unit}</BILLEDQTY>
                                </ALLINVENTORYENTRIES.LIST>
                            </VOUCHER>
                        </TALLYMESSAGE>
                    </REQUESTDATA>
                </IMPORTDATA>
            </BODY>
        </ENVELOPE>
        """
        return self.post_to_tally(xml_request.strip())


