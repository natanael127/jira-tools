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
PRJ_EXT = ".json"
PRJ_DIR = "projects/"
GIT_DIR = ".git/"

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
# --------------------- User authentication
if os.path.isfile(FILE_AUTH):
    with open(FILE_AUTH, "r") as fp:
        credentials = json.load(fp)
else:
    print("USER AUTHENTICATION: \n")
    credentials = {}
    credentials["server_url"] = input("Server URL: ")
    credentials["user_name"] = input("User name: ")
    credentials["api_key"] = input("API key: ")
    store_credentials = input("\nSave credentials to file? (Y/N): ")
    if store_credentials.lower() == "y":
        with open(FILE_AUTH, "w") as fp:
            json.dump(credentials, fp)

# --------------------- Choice or creation of project template
# Project listing
print("PROJECTS TEMPLATES: \n")
print("00 - Create new")
project_list = []
project_counter = 0
if not os.path.isdir(os.path.dirname(PRJ_DIR)):
    os.makedirs(os.path.dirname(PRJ_DIR))
for file_name in os.listdir(PRJ_DIR):
    project_list.append(file_name)
    project_counter += 1
    print(str(project_counter).zfill(2) + " - " + file_name.split(".")[0])

project_index = pyip.inputInt("\nChoose a number: ", min=0, max=len(project_list))
if project_index == 0:
    # Project insertion
    project_data = {}
    project_name = input("Project name: ")
    project_data["path"] = input("Path to repository: ")
    project_data["jira_abbrevs"] = []
    count_jira_abbrevs = 0
    print("Enter project keys (empty string to scape)")
    while True:
        jira_abbrev = input("Key #" + str(count_jira_abbrevs + 1) + ": ")
        if jira_abbrev != "":
            count_jira_abbrevs += 1
            project_data["jira_abbrevs"].append(jira_abbrev)
        else:
            break
    with open(PRJ_DIR + project_name + PRJ_EXT, "w") as fp:
        json.dump(project_data, fp)
else:
    # Project selection
    with open(PRJ_DIR + project_list[project_index - 1], "r") as fp:
        project_data = json.load(fp)

# --------------------- Repository reading
# Git objects initialization
repo = pygit2.Repository(project_data["path"] + GIT_DIR)
new_tag_str = "bm_hmi_sup_v421_r002" # TODO: prompt these values
old_tag_str = "BM_MM_v6.11r004"
new_commit, new_reference = repo.resolve_refish(new_tag_str)
old_commit, old_reference = repo.resolve_refish(old_tag_str)
list_commits = list(repo.walk(new_reference.target, pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_TIME))
# Trim list of commits from new tag to old tag only
for index_commit in range(len(list_commits)):
    if list_commits[index_commit].hex == old_commit.hex:
        break
list_commits = list_commits[:index_commit + 1]

# Tests
if False:
    jira_obj = get_jira_issue(credentials, "BM-160")
    with open(FILE_DEBUG, "w") as fp:
        json.dump(jira_obj, fp)
    print(jira_obj["fields"]["summary"])
