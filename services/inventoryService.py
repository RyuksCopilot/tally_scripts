# import requests
# import re
# import uuid
# from datetime import datetime


# class TallyInventoryManagement:
#     def __init__(self, tally_url="http://localhost:9000"):
#         self.tally_url = tally_url

#     # ---------- Utilities ----------
#     def to_snake_case(self, value: str) -> str:
#         """Convert string to snake_case for GUIDs or identifiers"""
#         value = re.sub(r'[\s-]+', '_', value)
#         value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
#         return value

#     def generate_guid(self, item_name: str, date: str) -> str:
#         """Generate a unique GUID using item name + date + UUID"""
#         item_key = self.to_snake_case(item_name)
#         return f"{item_key}_{date}"

#     def post_to_tally(self, xml_string: str):
#         """Send XML payload to Tally"""
#         headers = {"Content-Type": "application/xml"}
#         try:
#             response = requests.post(
#                 self.tally_url, data=xml_string.encode("utf-8"), headers=headers, timeout=10
#             )
#             return {"status": response.status_code, "response": response.text}
#         except requests.exceptions.RequestException as e:
#             return {"error": str(e)}

#     # ---------- Stock Item ----------
#     def create_stock_item(self, company_name, item_name, parent_group, unit, opening_balance=0):
#         """Create a stock item in Tally"""
#         xml_request = f"""
#         <ENVELOPE>
#             <HEADER>
#                 <TALLYREQUEST>Import Data</TALLYREQUEST>
#             </HEADER>
#             <BODY>
#                 <IMPORTDATA>
#                     <REQUESTDESC>
#                         <REPORTNAME>All Masters</REPORTNAME>
#                         <STATICVARIABLES>
#                             <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
#                         </STATICVARIABLES>
#                     </REQUESTDESC>
#                     <REQUESTDATA>
#                         <TALLYMESSAGE xmlns:UDF="TallyUDF">
#                             <STOCKITEM NAME="{item_name}" ACTION="Create">
#                                 <NAME.LIST>
#                                     <NAME>{item_name}</NAME>
#                                 </NAME.LIST>
#                                 <PARENT>{parent_group}</PARENT>
#                                 <BASEUNITS>{unit}</BASEUNITS>
#                                 <OPENINGBALANCE>{opening_balance}</OPENINGBALANCE>
#                             </STOCKITEM>
#                         </TALLYMESSAGE>
#                     </REQUESTDATA>
#                 </IMPORTDATA>
#             </BODY>
#         </ENVELOPE>
#         """
#         return self.post_to_tally(xml_request.strip())

#     # ---------- Stock Journal ----------
#     def create_stock_journal(
#         self, company_name, narration, item_name, qty, unit, godown="Main Location", date=None
#     ):
#         """Create a stock journal entry in Tally with auto-generated GUID"""
#         if not date:
#             date = datetime.now().strftime("%Y%m%d")  # default = today's date

#         voucher_guid = self.generate_guid(item_name, date)

#         xml_request = f"""
#         <ENVELOPE>
#             <HEADER>
#                 <TALLYREQUEST>Import Data</TALLYREQUEST>
#             </HEADER>
#             <BODY>
#                 <IMPORTDATA>
#                     <REQUESTDESC>
#                         <REPORTNAME>Vouchers</REPORTNAME>
#                         <STATICVARIABLES>
#                             <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
#                         </STATICVARIABLES>
#                     </REQUESTDESC>
#                     <REQUESTDATA>
#                         <TALLYMESSAGE xmlns:UDF="TallyUDF">
#                             <VOUCHER REMOTEID="{voucher_guid}" VCHTYPE="Stock Journal" ACTION="Create">
#                                 <DATE>{date}</DATE>
#                                 <VOUCHERTYPENAME>Stock Journal</VOUCHERTYPENAME>
#                                 <NARRATION>{narration}</NARRATION>

#                                 <!-- Inward Entry -->
#                                 <INVENTORYENTRIESIN.LIST>
#                                     <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
#                                     <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
#                                     <DESTINATIONGODOWN>{godown}</DESTINATIONGODOWN>
#                                     <ACTUALQTY>{qty} {unit}</ACTUALQTY>
#                                     <BILLEDQTY>{qty} {unit}</BILLEDQTY>
#                                 </INVENTORYENTRIESIN.LIST>

#                                 <!-- Outward Entry -->
#                                 <ALLINVENTORYENTRIES.LIST>
#                                     <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
#                                     <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
#                                     <SOURCEDGODOWN>{godown}</SOURCEDGODOWN>
#                                     <ACTUALQTY>{qty} {unit}</ACTUALQTY>
#                                     <BILLEDQTY>{qty} {unit}</BILLEDQTY>
#                                 </ALLINVENTORYENTRIES.LIST>
#                             </VOUCHER>
#                         </TALLYMESSAGE>
#                     </REQUESTDATA>
#                 </IMPORTDATA>
#             </BODY>
#         </ENVELOPE>
#         """
#         return self.post_to_tally(xml_request.strip())


import requests
import re
import xml.etree.ElementTree as ET
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
        """Generate a unique GUID using item name + date"""
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

    def clean_invalid_xml_chars(self, xml_str):
        """Remove invalid XML control characters like &#4; that Tally sometimes sends."""
        return re.sub(r"&#\d+;", "", xml_str)

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
        result = self.post_to_tally(xml_request.strip())

        # Fetch updated stock for this item
        stock_items = self.fetch_all_stock_items(company_name)
        latest_qty = next((i["closing_balance"] for i in stock_items if i["name"] == item_name), None)

        return {"tally_response": result, "closing_balance": latest_qty}

    # ---------- Stock Journal ----------
    def create_stock_journal(
        self, company_name, narration, item_name, qty, unit, godown="Main Location", date=None
    ):
        """Create a stock journal entry in Tally with auto-generated GUID"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")

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

                                <INVENTORYENTRIESIN.LIST>
                                    <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
                                    <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                    <DESTINATIONGODOWN>{godown}</DESTINATIONGODOWN>
                                    <ACTUALQTY>{qty} {unit}</ACTUALQTY>
                                    <BILLEDQTY>{qty} {unit}</BILLEDQTY>
                                </INVENTORYENTRIESIN.LIST>

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
        result = self.post_to_tally(xml_request.strip())

        # Fetch updated stock for this item
        stock_items = self.fetch_all_stock_items(company_name)
        latest_qty = next((i["closing_balance"] for i in stock_items if i["name"] == item_name), None)

        return {"tally_response": result, "closing_balance": latest_qty}

    # ---------- Fetch Stock Items ----------
    def fetch_all_stock_items(self, company_name):
        """Fetch all stock items from Tally with closing balance"""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>StockItems</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                    <TDL>
                        <TDLMESSAGE>
                            <COLLECTION NAME="StockItems" ISMODIFY="No" ISFIXED="No" ISINITIALIZE="No" ISOPTION="No" ISINTERNAL="No">
                                <TYPE>Stock Item</TYPE>
                                <FETCH>Name,Parent,ClosingBalance,BaseUnits</FETCH>
                            </COLLECTION>
                        </TDLMESSAGE>
                    </TDL>
                </DESC>
            </BODY>
        </ENVELOPE>
        """

        response = requests.post(self.tally_url, data=xml_request.encode("utf-8"))

        if response.status_code == 200 and response.text.strip() != "<ENVELOPE></ENVELOPE>":
            cleaned_xml = self.clean_invalid_xml_chars(response.text)
            root = ET.fromstring(cleaned_xml)
            stock_items = []

            for item in root.findall(".//STOCKITEM"):
                stock_items.append({
                    "name": item.get("NAME"),
                    "parent": item.findtext("PARENT"),
                    "unit": item.findtext("BASEUNITS"),
                    "closing_balance": item.findtext("CLOSINGBALANCE")
                })

            return stock_items
        else:
            return []
