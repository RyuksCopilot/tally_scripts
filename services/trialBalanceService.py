import requests
import xml.etree.ElementTree as ET

class TallyTrialBalanceManager:
    def __init__(self, tally_url: str):
        self.tally_url = tally_url
        self.required_fields = ["company_name"]
        self.all_fields = ["company_name"]

    def validate_input(self, data: dict):
        """Validate required input before making request."""
        for field in self.required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        return True

    def build_xml(self, data: dict):
        """Builds the XML for Trial Balance request."""
        return f"""
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <EXPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Trial Balance</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>{data['company_name']}</SVCURRENTCOMPANY>
                    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                    <EXPLODEFLAG>Yes</EXPLODEFLAG>
                </STATICVARIABLES>
            </REQUESTDESC>
        </EXPORTDATA>
    </BODY>
</ENVELOPE>
""".strip()

    def post_to_tally(self, xml_string):
        """Send XML to Tally and return response text."""
        headers = {"Content-Type": "application/xml"}
        try:
            response = requests.post(
                self.tally_url,
                data=xml_string.encode("utf-8"),
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.text
            else:
                raise Exception(f"Tally returned {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to communicate with Tally server: {e}")

    def parse_response(self, xml_string):
        """Parses Trial Balance XML into JSON list."""
        try:
            root = ET.fromstring(xml_string)
            data = []

            acc_names = root.findall(".//DSPACCNAME/DSPDISPNAME")
            acc_infos = root.findall(".//DSPACCINFO")

            for name_elem, info_elem in zip(acc_names, acc_infos):
                ledger_name = name_elem.text.strip() if name_elem.text else ""
                debit_elem = info_elem.find(".//DSPCLDRAMTA")
                credit_elem = info_elem.find(".//DSPCLCRAMTA")

                debit = debit_elem.text.strip() if debit_elem is not None and debit_elem.text else "0"
                credit = credit_elem.text.strip() if credit_elem is not None and credit_elem.text else "0"

                data.append({
                    "ledger_name": ledger_name,
                    "debit": float(debit) if debit else 0.0,
                    "credit": float(credit) if credit else 0.0
                })

            return data
        except ET.ParseError as e:
            raise Exception(f"Error parsing XML: {e}")

    def get_trial_balance(self, data: dict):
        """Validate, build request, fetch from Tally, and parse JSON."""
        self.validate_input(data)
        xml_request = self.build_xml(data)
        xml_response = self.post_to_tally(xml_request)
        return self.parse_response(xml_response)
