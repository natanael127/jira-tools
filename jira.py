# Based on https://developer.atlassian.com/cloud/jira/platform/rest/v3/

import pyinputplus
import requests
import json
import os

def auth_prompt_or_restore(auth_file="authentication.json"):
    credentials = {}
    if os.path.isfile(auth_file):
        with open(auth_file, "r") as fp:
            credentials = json.load(fp)
    else:
        print("USER AUTHENTICATION")
        credentials["server_url"] = input("Server URL: ")
        credentials["user_name"] = input("API user (your e-mail): ")
        credentials["api_key"] = input("API key (https://id.atlassian.com/manage-profile/security/api-tokens): ")
        store_credentials = pyinputplus.inputYesNo("\nSave credentials to file? (Y/N): ")
        if store_credentials == "yes":
            with open(auth_file, "w") as fp:
                json.dump(credentials, fp, indent=4)
    return credentials

class api:
    def __init__(self, server_url : str, user_email : str, api_key : str, cache_dir : str="jira_cache" ):
        self.__server_url = server_url
        if not server_url.endswith("/"):
            self.__server_url = server_url + "/"
        self.__user_email = user_email
        self.__api_key = api_key
        self.__cache_dir = cache_dir

    def get_issue(self, issue_key_or_id, cache_use=False):
        output = {}
        if not cache_use:
            try:
                request_url = self.__server_url + "rest/api/3/issue/" + issue_key_or_id
                resp = requests.get(request_url, auth=(self.__user_email, self.__api_key))
                output = resp.json()
            except KeyboardInterrupt:
                exit()
            except:
                pass
        else:
            # Creates cache dir if does not exist
            issue_cache_dir = os.path.join(self.__cache_dir, "issue")
            if not os.path.isdir(issue_cache_dir):
                os.makedirs(issue_cache_dir)
            # Verify cache
            issue_file = os.path.join(issue_cache_dir, issue_key_or_id + ".json")
            if os.path.isfile(issue_file):
                # Restore from file
                with open(issue_file, "r") as fp:
                    output = json.load(fp)
            else:
                # Download data
                try:
                    request_url = self.__server_url + "rest/api/3/issue/" + issue_key_or_id
                    resp = requests.get(request_url, auth=(self.__user_email, self.__api_key))
                    output = resp.json()
                except KeyboardInterrupt:
                    exit()
                except:
                    pass
                # Create files for key and id
                with open(os.path.join(issue_cache_dir, output["key"] + ".json"), "w") as fp:
                    json.dump(output, fp)
                with open(os.path.join(issue_cache_dir, output["id"] + ".json"), "w") as fp:
                    json.dump(output, fp)
        return output

    def get_worklog(self, worklog_id_or_list, cache_use=False):
        output = []
        # Transforms to list
        if type(worklog_id_or_list) != type([]):
            worklog_id_or_list = [worklog_id_or_list]
        # Transforms to list of integers
        list_worklog_ids = list(map(int, worklog_id_or_list))
        # Handle cached or uncached decision
        if not cache_use:
            try:
                request_url = self.__server_url + "rest/api/3/worklog/list"
                resp = requests.post(request_url, auth=(self.__user_email, self.__api_key), json={"ids": list_worklog_ids})
                output = resp.json()
            except KeyboardInterrupt:
                exit()
            except:
                pass
        else:
            # Creates cache dir if does not exist
            worklog_cache_dir = os.path.join(self.__cache_dir, "worklog")
            if not os.path.isdir(worklog_cache_dir):
                os.makedirs(worklog_cache_dir)
            # Initialize control lists
            list_cached_data = []
            list_uncached_data = []
            list_ids_to_remove = []
            # Look for cached files
            for worklog_id in list_worklog_ids:
                worklog_file = os.path.join(worklog_cache_dir, str(worklog_id) + ".json")
                if os.path.isfile(worklog_file):
                    list_ids_to_remove.append(worklog_id)
                    with open(worklog_file, "r") as fp:
                        list_cached_data.append(json.load(fp))
            # Update list to be caught in the web
            list_worklog_ids = list(set(list_worklog_ids) - set(list_ids_to_remove))
            # Get remaining worklogs in the web
            if len(list_worklog_ids) > 0:
                try:
                    request_url = self.__server_url + "rest/api/3/worklog/list"
                    resp = requests.post(request_url, auth=(self.__user_email, self.__api_key), json={"ids": list_worklog_ids})
                    list_uncached_data = resp.json()
                    # Save downloaded data to files
                    for downloaded_data in list_uncached_data:
                        worklog_id = downloaded_data["id"]
                        worklog_file = os.path.join(worklog_cache_dir, str(worklog_id) + ".json")
                        with open(worklog_file, "w") as fp:
                            json.dump(downloaded_data, fp)
                except KeyboardInterrupt:
                    exit()
                except:
                    pass
            output = list_uncached_data + list_cached_data
        return output
