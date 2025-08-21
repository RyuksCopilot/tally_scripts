import requests

class TallyGroupService:
    def __init__(self, tally_url="http://localhost:9000"):
        self.tally_url = tally_url
        self.required_fields_create = ["company_name", "group_name", "parent_group"]
        self.required_fields_delete = ["company_name", "group_name"]
        self.all_fields_create = ["company_name", "group_name", "parent_group", "nature_of_group"]
        self.all_fields_delete = ["company_name", "group_name"]

    def validate_input(self, data: dict, required_fields: list, all_fields: list):
        """
        Validate required and allowed fields
        """
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        unknown = [f for f in data.keys() if f not in all_fields]
        if unknown:
            raise ValueError(f"Invalid fields provided: {', '.join(unknown)}")

        return True

    def build_xml(self, data: dict, action="CREATE"):
        """
        Build XML payload for CREATE, DELETE or ALTER
        """
        if action.upper() == "DELETE":
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
                    <SVCURRENTCOMPANY>{data['company_name']}</SVCURRENTCOMPANY>
                </STATICVARIABLES>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <GROUP NAME="{data['group_name']}" ACTION="Delete">
                        <NAME>{data['group_name']}</NAME>
                    </GROUP>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>
"""
        else:  # CREATE or ALTER
            nature_of_group = data.get("nature_of_group", "Assets")
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
                    <SVCURRENTCOMPANY>{data['company_name']}</SVCURRENTCOMPANY>
                </STATICVARIABLES>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <GROUP NAME="{data['group_name']}" ACTION="{action}">
                        <NAME>{data['group_name']}</NAME>
                        <PARENT>{data['parent_group']}</PARENT>
                        <NATUREOFGROUP>{nature_of_group}</NATUREOFGROUP>
                    </GROUP>
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

    def create_group(self, data: dict, action="CREATE"):
        """
        Create a Group
        """
        self.validate_input(data, self.required_fields_create, self.all_fields_create)
        xml_payload = self.build_xml(data, action=action)
        return self.post_to_tally(xml_payload)

    def delete_group(self, data: dict):
        """
        Delete a Group
        """
        self.validate_input(data, self.required_fields_delete, self.all_fields_delete)
        xml_payload = self.build_xml(data, action="DELETE")
        return self.post_to_tally(xml_payload)
