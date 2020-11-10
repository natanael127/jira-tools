# ===================== IMPORTS ============================================== #
from http.client import HTTPSConnection
from base64 import b64encode
import json
import pygit2

# ===================== CONSTANTS ============================================ #
FILE_AUTH = "authentication.json"

# ===================== AUXILIAR FUNCTIONS =================================== #
def get_jira_issue(auth_obj, issue_key):
    conn = HTTPSConnection(auth_obj["server_url"])
    auth_string = auth_obj["user_name"] + ":" + auth_obj["api_key"]
    userAndPass = b64encode(bytearray(auth_string, "utf-8")).decode("utf-8")
    hdrs = { "Authorization" : "Basic " + userAndPass }
    conn.request("GET", "/rest/api/3/issue/" + issue_key, headers=hdrs)
    res = conn.getresponse()
    raw_data = res.read().decode("utf-8")
    return json.loads(raw_data)

# ===================== MAIN SCRIPT ========================================== #
with open(FILE_AUTH, "r") as fp:
    credentials = json.load(fp)
jira_obj = get_jira_issue(credentials, "BM-160")
print(jira_obj["fields"]["summary"])


