import requests
import xml.etree.ElementTree as ET
import json


class TallyLedgerFetcher:
    def __init__(self, tally_url: str):
        self.tally_url = tally_url
        
    def _get_ledger_vouchers_xml(self,company_name:str,ledger_name: str) -> str:
        """
        Creates XML request to fetch all transactions for a specific ledger.
        """
        return f"""
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <EXPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Ledger Vouchers</REPORTNAME>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
                    <LEDGERNAME>{ledger_name}</LEDGERNAME>
                    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                </STATICVARIABLES>
            </REQUESTDESC>
        </EXPORTDATA>
    </BODY>
</ENVELOPE>
"""

    def fetch_ledger_vouchers(self, company_name:str,ledger_name: str) -> str | None:
        """
        Send request to Tally and fetch ledger vouchers XML.
        """
        xml_request = self._get_ledger_vouchers_xml(company_name,ledger_name)
        headers = {"Content-Type": "application/xml"}

        try:
            response = requests.post(
                self.tally_url, 
                data=xml_request.encode("utf-8"), 
                headers=headers, 
                timeout=10
            )
            if response.status_code == 200:
                return response.text
            else:
                print("Error from Tally:", response.status_code, response.text)
                return None
        except requests.exceptions.RequestException as e:
            print("Failed to communicate with Tally server:", e)
            return None

    def parse_vouchers(self, xml_response: str) -> list[dict]:
        """
        Parse XML response and return a list of transactions in JSON-like dicts.
        """
        transactions = []
        try:
            root = ET.fromstring(xml_response)
            # Iterate over repeating tags
            dates = root.findall("DSPVCHDATE")
            accounts = root.findall("DSPVCHLEDACCOUNT")
            types = root.findall("DSPVCHTYPE")
            dr_amounts = root.findall("DSPVCHDRAMT")
            cr_amounts = root.findall("DSPVCHCRAMT")

            for i in range(len(dates)):
                transaction = {
                    "date": dates[i].text,
                    "ledger": accounts[i].text,
                    "voucher_type": types[i].text,
                    "debit": dr_amounts[i].text if dr_amounts[i].text else "0",
                    "credit": cr_amounts[i].text if cr_amounts[i].text else "0",
                }
                transactions.append(transaction)
        except ET.ParseError as e:
            print("Error parsing XML:", e)

        return transactions

    def get_ledger_transactions(self, company_name: str, ledger_name: str) -> list[dict]:
        """
        Fetch transactions for a ledger and return list of dicts.
        """
        xml_response = self.fetch_ledger_vouchers(company_name, ledger_name)
        if xml_response:
            return self.parse_vouchers(xml_response)
        return []

