import requests
import xml.etree.ElementTree as ET
import json


class TallyBalanceSheetFetcher:
    def __init__(self, tally_url: str):
        self.tally_url = tally_url

    def _get_balance_sheet_xml(self,company_name:str) -> str:
        return f"""
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <EXPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Balance Sheet</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
                    <EXPLODEALLLEVELS>Yes</EXPLODEALLLEVELS>
                    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                </STATICVARIABLES>
            </REQUESTDESC>
        </EXPORTDATA>
    </BODY>
</ENVELOPE>
"""

    def fetch_balance_sheet(self,company_name:str) -> str | None:
        xml_request = self._get_balance_sheet_xml(company_name)
        headers = {"Content-Type": "application/xml"}
        try:
            response = requests.post(
                self.tally_url, data=xml_request.encode("utf-8"),
                headers=headers, timeout=10
            )
            if response.status_code == 200:
                return response.text
            else:
                print("Error from Tally:", response.status_code, response.text)
                return None
        except requests.exceptions.RequestException as e:
            print("Failed to communicate with Tally server:", e)
            return None

    def parse_balance_sheet(self, xml_response: str) -> list[dict]:
        """
        Parse Balance Sheet XML response into structured list of dicts.
        Matches <BSNAME> with following <BSAMT>.
        """
        balances = []
        try:
            root = ET.fromstring(xml_response)
            bs_names = root.findall("BSNAME")
            bs_amts = root.findall("BSAMT")

            for i in range(min(len(bs_names), len(bs_amts))):
                name_node = bs_names[i].find(".//DSPDISPNAME")
                sub_amt = bs_amts[i].find("BSSUBAMT")
                main_amt = bs_amts[i].find("BSMAINAMT")

                account = name_node.text.strip() if (name_node is not None and name_node.text) else "Unknown"
                balance = None
                if sub_amt is not None and sub_amt.text:
                    balance = sub_amt.text.strip()
                elif main_amt is not None and main_amt.text:
                    balance = main_amt.text.strip()
                else:
                    balance = "0"

                balances.append({
                    "account": account,
                    "closing_balance": balance
                })

        except ET.ParseError as e:
            print("Error parsing XML:", e)

        return balances

    def get_balance_sheet(self,company_name:str) -> list[dict]:
        xml_response = self.fetch_balance_sheet(company_name)
        if xml_response:
            return self.parse_balance_sheet(xml_response)
        return []

