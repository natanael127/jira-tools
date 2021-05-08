# ===================== IMPORTS ============================================== #
from http.client import HTTPSConnection
from base64 import b64encode
import json
import pygit2
import os
import pyinputplus as pyip
import csv

# ===================== CONSTANTS ============================================ #
FILE_AUTH = "authentication.json"
PRJ_EXT = ".json"
PRJ_DIR = "projects/"
GIT_DIR = ".git/"
N_BARS_PROGRESS = 30

# ===================== AUXILIAR FUNCTIONS =================================== #
def create_progress_bar(fraction, number_of_bars):
    str_output = "|"
    for bar_counter in range(number_of_bars):
        if (bar_counter + 1) / number_of_bars <= fraction:
            str_output += "\u2588"
        else:
            str_output += " "
    str_output += "| " + str(int(fraction * 100)).rjust(3) + "%"
    return str_output

def get_jira_issue(auth_obj, issue_key):
    conn = HTTPSConnection(auth_obj["server_url"])
    auth_string = auth_obj["user_name"] + ":" + auth_obj["api_key"]
    user_and_pass = b64encode(bytearray(auth_string, "utf-8")).decode("utf-8")
    hdrs = { "Authorization" : "Basic " + user_and_pass }
    conn.request("GET", "/rest/api/3/issue/" + issue_key, headers=hdrs)
    res = conn.getresponse()
    raw_data = res.read().decode("utf-8")
    return json.loads(raw_data)

def extract_jira_issues_from_string(content, list_of_abbrev):
    import re
    # Compose the regex string
    str_regex = "(\W|^)("
    for jira_abbrev in list_of_abbrev:
        str_regex += jira_abbrev + "|"
    str_regex += ")(-)(\d+)"
    # Get a list of matches like tupple
    list_matches = re.findall(str_regex, content)
    list_result = []
    # Turns the tupple in string
    for element in list_matches:
        list_result.append("".join(list(element[1:])))
    return list_result

def print_title_section(string_to_print):
    print("=====================================================")
    print(string_to_print)
    print()
                

# ===================== MAIN SCRIPT ========================================== #
# --------------------- User authentication
if os.path.isfile(FILE_AUTH):
    with open(FILE_AUTH, "r") as fp:
        credentials = json.load(fp)
else:
    print_title_section("USER AUTHENTICATION")
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
print_title_section("PROJECTS TEMPLATES")
print("00 - Create new")
project_list = []
project_counter = 0
if not os.path.isdir(os.path.dirname(PRJ_DIR)):
    os.makedirs(os.path.dirname(PRJ_DIR))
for file_name in os.listdir(PRJ_DIR):
    if os.path.isfile(PRJ_DIR + file_name):
        project_list.append(file_name)
        project_counter += 1
        print(str(project_counter).zfill(2) + " - " + file_name.split(".")[0])

project_index = pyip.inputInt("\nChoose a number: ", min=0, max=len(project_list))
if project_index == 0:
    # Project insertion
    print_title_section("NEW PROJECT")
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
print_title_section("GIT REFERENCES (tag, commit or branch)")
repo = pygit2.Repository(project_data["path"] + GIT_DIR)
new_ref_str = input("Newest reference: ")
old_ref_str = input("Oldest reference: ")
new_commit, new_reference = repo.resolve_refish(new_ref_str)
old_commit, old_reference = repo.resolve_refish(old_ref_str)
list_commits = []
list_commits_new = list(repo.walk(new_reference.target, pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_TIME))
list_commits_old = list(repo.walk(old_reference.target, pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_TIME))
# Find commits ahead in newest reference
for commit_obj in list_commits_new:
    if commit_obj not in list_commits_old:
        list_commits.append(commit_obj)
# Search for jira keys
list_keys = []
for commit_obj in list_commits:
    # Find Jira keys
    list_found_keys_commit = extract_jira_issues_from_string(commit_obj.message, project_data["jira_abbrevs"])
    for found_key_commit in list_found_keys_commit:
        if found_key_commit not in [d["jira-key"] for d in list_keys if "jira-key" in d]:
            list_keys.append({"jira-key": found_key_commit, "last-update": commit_obj.commit_time})

# --------------------- Issues validation using Jira API
# Lists valid issues
print_title_section("Downloading info from Jira...")
list_valid_issues = []
for count_elements, element in enumerate(list_keys):
    print("Progress: " + create_progress_bar((count_elements + 1) / len(list_keys), N_BARS_PROGRESS), end="\r")
    # Download and parse
    jira_dict = get_jira_issue(credentials, element["jira-key"])
    if "errorMessages" not in jira_dict.keys():
        customized_dict = {}
        customized_dict["Jira key"] = element["jira-key"]
        customized_dict["Type"] = jira_dict["fields"]["issuetype"]["name"]
        customized_dict["Timestamp"] = element["last-update"]
        customized_dict["Summary"] = jira_dict["fields"]["summary"]
        try:
            customized_dict["Assignee"] = jira_dict["fields"]["assignee"]["displayName"]
        except:
            customized_dict["Assignee"] = ""
        list_valid_issues.append(customized_dict)

# Dumps to a csv
csv_keys = list_valid_issues[0].keys()
file_name_output = "FROM " + old_ref_str + " TO " + new_ref_str + ".csv"
with open(file_name_output,"w", newline='') as fp:
    dict_writer = csv.DictWriter(fp, csv_keys, delimiter=",", quotechar="\"", quoting=csv.QUOTE_NONNUMERIC)
    dict_writer.writeheader()
    dict_writer.writerows(list_valid_issues)

# Informs the end
print("\nDone!")
