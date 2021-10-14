# ===================== IMPORTS ============================================== #
import pyinputplus
import jira
import copy
import csv
import sys
from dateutil import parser

# ===================== AUXILIARY FUNCTIONS ================================== #
def create_progress_bar(fraction, number_of_bars):
    str_output = "|"
    for bar_counter in range(number_of_bars):
        if (bar_counter + 1) / number_of_bars <= fraction:
            str_output += "\u2588"
        else:
            str_output += " "
    str_output += "| " + str(int(fraction * 100)).rjust(3) + "%"
    return str_output

# ===================== MAIN SCRIPT ========================================== #
# Jira authentication data
credentials = jira.auth_prompt_or_restore()
jira_conn = jira.api(credentials["server_url"], credentials["user_name"], credentials["api_key"])
# Interest data structure
dummy_item = {"work_id": 0, "user": "", "jira_key": "", "time_spent_hours": 0.0, "date": "", "description": ""}
# Parameters to sweep
if len(sys.argv) > 1:
    first_worklog = int(sys.argv[1])
else:
    first_worklog = pyinputplus.inputInt("First worklog id: ", min=0)
group_worklog = 1000
# Initializations for loop
number_of_results = 1
list_interest = []
# Iterative loop
while number_of_results > 0:
    result = jira_conn.get_worklog(list(range(first_worklog, first_worklog + group_worklog)), cache_use=True)
    number_of_results = len(result)
    if number_of_results != 0:
        print(f"\nDownloading {number_of_results} elements between {first_worklog} and {first_worklog + group_worklog - 1}")
    for count_elements, worklog in enumerate(result):
        print(">>>   " + create_progress_bar((count_elements + 1) / number_of_results, 30), end="\r")
        item_interest = copy.deepcopy(dummy_item)
        try:
            item_interest["work_id"] = int(worklog["id"])
        except:
            pass
        try:
            item_interest["user"] = worklog["author"]["emailAddress"]
        except:
            pass
        issue_id = jira_conn.get_issue(worklog["issueId"], cache_use=True)["key"]
        try:
            item_interest["jira_key"] = issue_id
        except:
            pass
        try:
            item_interest["time_spent_hours"] = worklog["timeSpentSeconds"] / 3600
        except:
            pass
        try:
            item_interest["date"] = parser.isoparse(worklog["started"]).strftime("%Y-%m-%d")
        except:
            pass
        if worklog.get("comment", {}).get("content") != None:
            list_phrases = []
            for content in worklog.get("comment").get("content"):
                phrase = ""
                for subcontent in content["content"]:
                    try:
                        phrase += subcontent["text"]
                    except:
                        pass
                list_phrases.append(phrase)
            item_interest["description"] = " ".join(list_phrases)
        list_interest.append(item_interest)
    first_worklog += group_worklog
print()

# Sort the list by work id
list_interest = sorted(list_interest, key=lambda d: d["work_id"])
# Dump to CSV
csv_keys = list_interest[0].keys()
with open("output.csv","w", newline="", encoding="utf-8") as fp:
    dict_writer = csv.DictWriter(fp, csv_keys, delimiter=",", quotechar="\"", quoting=csv.QUOTE_NONNUMERIC, extrasaction="ignore")
    dict_writer.writeheader()
    dict_writer.writerows(list_interest)