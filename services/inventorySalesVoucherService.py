import requests
import re

class TallySalesVoucherManager:
    def __init__(self, tally_url="http://localhost:9000"):
        self.tally_url = tally_url
        self.required_fields = [
            "company_name", "customer_ledger", "sales_ledger",
            "items", "date"
        ]
        self.all_fields = self.required_fields + ["narration", "voucher_guid"]

    def validate_input(self, data: dict):
        """Validate required input fields for sales voucher."""
        for field in self.required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(data["items"], list) or not data["items"]:
            raise ValueError("Items must be a non-empty list")

        for item in data["items"]:
            for key in ["name", "qty", "rate", "unit"]:
                if key not in item or not item[key]:
                    raise ValueError(f"Missing {key} in items")
            try:
                float(item["qty"])
                float(item["rate"])
            except ValueError:
                raise ValueError("Qty and Rate must be numeric")

        if not re.match(r"^\d{8}$", str(data["date"])):
            raise ValueError("Date must be in YYYYMMDD format")

        return True

    def build_voucher_guid(self, customer_ledger, sales_ledger, total_amount, date):
        return f"{customer_ledger}_{sales_ledger}_{total_amount}_Sales_{date}"

    def build_xml(self, data: dict, action="Create"):
        """Build XML request for Sales Voucher with inventory."""
        # Calculate total amount
        total_amount = sum(item["qty"] * item["rate"] for item in data["items"])

        voucher_guid = data.get("voucher_guid") or self.build_voucher_guid(
            data["customer_ledger"], data["sales_ledger"], total_amount, data["date"]
        )

        narration = data.get("narration") or f"Sales to {data['customer_ledger']}"

        # Build inventory XML
        inventory_xml = ""
        for item in data["items"]:
            amount = item["qty"] * item["rate"]
            inventory_xml += f"""
            <ALLINVENTORYENTRIES.LIST>
                <STOCKITEMNAME>{item['name']}</STOCKITEMNAME>
                <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> <!-- Stock goes out -->
                <RATE>{item['rate']} / {item['unit']}</RATE>
                <ACTUALQTY>{item['qty']} {item['unit']}</ACTUALQTY>
                <BILLEDQTY>{item['qty']} {item['unit']}</BILLEDQTY>
                <AMOUNT>{amount}</AMOUNT>

                <!-- Sales Ledger -->
                <ACCOUNTINGALLOCATIONS.LIST>
                    <LEDGERNAME>{data['sales_ledger']}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE> <!-- Income -->
                    <AMOUNT>{amount}</AMOUNT>
                </ACCOUNTINGALLOCATIONS.LIST>
                
                <ACCOUNTINGALLOCATIONS.LIST>
                    <LEDGERNAME>{data['customer_ledger']}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> <!-- Income -->
                    <AMOUNT>-{amount}</AMOUNT>
                </ACCOUNTINGALLOCATIONS.LIST>
            </ALLINVENTORYENTRIES.LIST>
            """

        # Complete XML envelope
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
                    <VOUCHER REMOTEID="{voucher_guid}" VCHTYPE="Sales"
                             ACTION="{action.capitalize()}" OBJVIEW="Inventory Voucher View">
                        <DATE>{data['date']}</DATE>
                        <EFFECTIVEDATE>{data['date']}</EFFECTIVEDATE>
                        <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                        <NARRATION>{narration}</NARRATION>
                        <PARTYLEDGERNAME>{data['customer_ledger']}</PARTYLEDGERNAME>
                        {inventory_xml}
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


# if __name__ == "__main__":
#     manager = TallySalesVoucherManager()

#     sales_data = {
#         "company_name": "RYUKS",
#         "customer_ledger": "AKASH LTD",
#         "sales_ledger": "SALES A/C",
#         "items": [
#             {"name": "ITEM 1", "qty": 10, "rate": 50, "unit": "Nos"}
#         ],
#         "date": "20250401",
#         "narration": "Sales to Rahul Ltd"
#     }

#     response = manager.save_voucher(sales_data)
#     print("Response from Tally:", response)
