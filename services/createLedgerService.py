import requests
import re

class TallyLedgerManager:
    def __init__(self, tally_url="http://localhost:9000"):
        self.tally_url = tally_url
        self.required_fields = ["ledger_name", "group_name", "company_name"]
        self.all_fields = [
            "ledger_name", "group_name", "company_name", "mailing_name", "address_list",
            "pincode", "state", "country", "email", "phone", "opening_balance"
        ]

    def validate_input(self, data: dict):
        for field in self.required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        if data.get("email") and not re.match(r"[^@]+@[^@]+\.[^@]+", data["email"]):
            raise ValueError("Invalid email format")
        if data.get("pincode") and (not data["pincode"].isdigit() or len(data["pincode"]) != 6):
            raise ValueError("Pincode must be a 6-digit number")
        if data.get("phone") and (not data["phone"].isdigit() or len(data["phone"]) < 7):
            raise ValueError("Phone number must be numeric and at least 7 digits long")
        if data.get("opening_balance"):
            try:
                float(data["opening_balance"])
            except ValueError:
                raise ValueError("Opening balance must be a number")
        return True

    def build_xml(self, data: dict, action="CREATE"):
        mailing_details_xml = ""
        if data.get("mailing_name"):
            mailing_details_xml += f"""
            <MAILINGNAME.LIST>
                <MAILINGNAME>{data['mailing_name']}</MAILINGNAME>
            </MAILINGNAME.LIST>
            """
        if data.get("address_list"):
            mailing_details_xml += '<ADDRESS.LIST TYPE="String">\n'
            for addr in data["address_list"]:
                mailing_details_xml += f"    <ADDRESS>{addr}</ADDRESS>\n"
            mailing_details_xml += "</ADDRESS.LIST>\n"
        if data.get("pincode"):
            mailing_details_xml += f"<PINCODE>{data['pincode']}</PINCODE>\n"
        if data.get("state"):
            mailing_details_xml += f"<STATENAME>{data['state']}</STATENAME>\n"
        if data.get("country"):
            mailing_details_xml += f"<COUNTRYNAME>{data['country']}</COUNTRYNAME>\n"
        if data.get("email"):
            mailing_details_xml += f"<EMAIL>{data['email']}</EMAIL>\n"
        if data.get("phone"):
            mailing_details_xml += f"<PHONENUMBER>{data['phone']}</PHONENUMBER>\n"
        if data.get("opening_balance"):
            mailing_details_xml += f"<OPENINGBALANCE>{data['opening_balance']}</OPENINGBALANCE>\n"

        xml = f"""
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>All Masters</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>{data.get("company_name", "")}</SVCURRENTCOMPANY>
                </STATICVARIABLES>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <LEDGER NAME="{data['ledger_name']}" ACTION="{action}">
                        <NAME>{data['ledger_name']}</NAME>
                        <PARENT>{data['group_name']}</PARENT>
                        <ISBILLWISEON>No</ISBILLWISEON>
                        <AFFECTSSTOCK>No</AFFECTSSTOCK>
                        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                        {mailing_details_xml}
                    </LEDGER>
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
            response = requests.post(self.tally_url, data=xml_string.encode("utf-8"), headers=headers, timeout=10)
            return {"status": response.status_code, "response": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def save_ledger(self, data: dict, action="CREATE"):
        self.validate_input(data)
        xml_payload = self.build_xml(data, action=action)
        return self.post_to_tally(xml_payload)
