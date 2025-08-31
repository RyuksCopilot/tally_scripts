import requests
import re

class TallyInventoryVoucherManager:
    def __init__(self, tally_url="http://localhost:9000"):
        self.tally_url = tally_url
        self.required_fields = [
            "company_name", "party_ledger", "purchase_ledger",
            "items", "date", "voucher_type"
        ]
        self.all_fields = self.required_fields + ["narration", "voucher_guid"]

    # ---------- Utilities ----------
    def to_snake_case(self, value: str) -> str:
        """Convert a string to snake_case."""
        value = re.sub(r'[\s-]+', '_', value)
        value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
        return value.lower()

    # ---------- Validation ----------
    def validate_input(self, data: dict):
        for field in self.required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(data["items"], list) or not data["items"]:
            raise ValueError("Items must be a non-empty list")

        for item in data["items"]:
            if not all(k in item for k in ["name", "qty", "rate", "unit"]):
                raise ValueError("Each item must have name, qty, rate, unit")

            try:
                float(item["qty"])
                float(item["rate"])
            except ValueError:
                raise ValueError("Item qty and rate must be numeric")

        if not re.match(r"^\d{8}$", str(data["date"])):
            raise ValueError("Date must be in YYYYMMDD format")

        return True

    # ---------- Voucher GUID ----------
    def build_voucher_guid(self, party_ledger, purchase_ledger, total_amount, voucher_type, date):
        return f"{self.to_snake_case(party_ledger)}_{self.to_snake_case(purchase_ledger)}_{total_amount}_{voucher_type}_{date}"

    # ---------- XML Builder ----------
    def build_xml(self, data: dict, action="Create"):
        total_amount = sum(item["qty"] * item["rate"] for item in data["items"])
        voucher_guid = data.get("voucher_guid") or self.build_voucher_guid(
            data["party_ledger"], data["purchase_ledger"], total_amount, data["voucher_type"], data["date"]
        )

        narration = data.get("narration") or f"Purchase from {data['party_ledger']}"

        # Build inventory entries XML
        inventory_xml = ""
        for item in data["items"]:
            amount = item["qty"] * item["rate"]
            inventory_xml += f"""
            <ALLINVENTORYENTRIES.LIST>
                <STOCKITEMNAME>{item['name']}</STOCKITEMNAME>
                <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                <RATE>{item['rate']} / {item['unit']}</RATE>
                <ACTUALQTY>{item['qty']} {item['unit']}</ACTUALQTY>
                <BILLEDQTY>{item['qty']} {item['unit']}</BILLEDQTY>
                <AMOUNT>{amount}</AMOUNT>
                
                <ACCOUNTINGALLOCATIONS.LIST>
                    <LEDGERNAME>{data['purchase_ledger']}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                    <AMOUNT>-{amount}</AMOUNT>
                </ACCOUNTINGALLOCATIONS.LIST>
                <ACCOUNTINGALLOCATIONS.LIST>
                    <LEDGERNAME>{data['party_ledger']}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                    <AMOUNT>{amount}</AMOUNT>
                </ACCOUNTINGALLOCATIONS.LIST>
            </ALLINVENTORYENTRIES.LIST>
            """

        # Complete XML
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
                             VCHTYPE="{data['voucher_type']}" 
                             ACTION="{action.capitalize()}" 
                             OBJVIEW="Inventory Voucher View">
                        <DATE>{data['date']}</DATE>
                        <EFFECTIVEDATE>{data['date']}</EFFECTIVEDATE>
                        <VOUCHERTYPENAME>{data['voucher_type']}</VOUCHERTYPENAME>
                        <PARTYLEDGERNAME>{data['party_ledger']}</PARTYLEDGERNAME>
                        <NARRATION>{narration}</NARRATION>
                        
                        {inventory_xml}
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>
"""
        return xml.strip()

    # ---------- Post to Tally ----------
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

    # ---------- Save Voucher ----------
    def save_voucher(self, data: dict, action="Create"):
        self.validate_input(data)
        xml_payload = self.build_xml(data, action=action)
        return self.post_to_tally(xml_payload)


# ---------- Example Usage ----------
# if __name__ == "__main__":
#     manager = TallyInventoryVoucherManager()

#     company = "RYUKS"
#     items = [
#         {"name": "ITEM 1", "qty": 10, "rate": 40, "unit": "Nos"},
#         {"name": "ITEM 4", "qty": 10, "rate": 50, "unit": "Nos"}
#     ]

#     data = {
#         "company_name": company,
#         "party_ledger": "AKASH LTD",
#         "purchase_ledger": "PURCHASE GOOD",
#         "items": items,
#         "date": "20250401",
#         "voucher_type": "Purchase",
#         "narration": "Inventory purchase from Vijay"
#     }

#     result = manager.save_voucher(data)
#     print(result)