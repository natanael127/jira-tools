# ===================== IMPORTS ============================================== #
from http.client import HTTPSConnection
from base64 import b64encode
import json
import pygit2
import os
import pyinputplus as pyip

# ===================== CONSTANTS ============================================ #
FILE_AUTH = "authentication.json"
FILE_DEBUG = "debug.json"
EXT_FILE_PRJ = ".json"
START_FILE_PRJ = "project_"

# ===================== AUXILIAR FUNCTIONS =================================== #
def get_jira_issue(auth_obj, issue_key):
    conn = HTTPSConnection(auth_obj["server_url"])
    auth_string = auth_obj["user_name"] + ":" + auth_obj["api_key"]
    user_and_pass = b64encode(bytearray(auth_string, "utf-8")).decode("utf-8")
    hdrs = { "Authorization" : "Basic " + user_and_pass }
    conn.request("GET", "/rest/api/3/issue/" + issue_key, headers=hdrs)
    res = conn.getresponse()
    raw_data = res.read().decode("utf-8")
    return json.loads(raw_data)

# ===================== MAIN SCRIPT ========================================== #
# User authentication
credentials = {}
if os.path.isfile(FILE_AUTH):
    with open(FILE_AUTH, "r") as fp:
        credentials = json.load(fp)
else:
    print("USER AUTHENTICATION: \n")
    credentials["server_url"] = input("Server URL: ")
    credentials["user_name"] = input("User name: ")
    credentials["api_key"] = input("API key: ")
    store_credentials = input("\nSave credentials to file? (Y/N): ")
    if store_credentials.lower() == "y":
        with open(FILE_AUTH, "w") as fp:
            json.dump(credentials, fp)

# Project selection
print("PROJECTS TEMPLATES: \n")
print("00 - Create new")
project_list = []
project_counter = 0
for file_name in os.listdir("./"):
    if os.path.isfile(file_name) and file_name.startswith(START_FILE_PRJ) and file_name.endswith(EXT_FILE_PRJ):
        project_list.append(file_name)
        project_counter += 1
        print(str(project_counter).zfill(2) + " - " + file_name[len(START_FILE_PRJ):-len(EXT_FILE_PRJ)])

project_index = pyip.inputInt("\nChoose a number: ", min=0, max=len(project_list))
if project_index == 0:
    pass
else:
    pass
# Tests
jira_obj = get_jira_issue(credentials, "BM-160")
with open(FILE_DEBUG, "w") as fp:
    json.dump(jira_obj, fp)
print(jira_obj["fields"]["summary"])
