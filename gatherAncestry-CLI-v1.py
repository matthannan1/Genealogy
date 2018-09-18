"""
31 May 2018
Matt Hannan
matthannan1@gmail.com
Based on this web site:
https://ianlondon.github.io/blog/web-scraping-discovering-hidden-apis/
I used his method and found match data here:
https://dnahomeaws.ancestry.com/dna/secure/tests/B0004280-63E9-45B2-9588-1E7AE812CC1D/matches?filterBy=ALL&sortBy=RELATIONSHIP&page=1
and Shared Match data here:
https://dnahomeaws.ancestry.com/dna/secure/tests/B0004280-63E9-45B2-9588-1E7AE812CC1D/matchesInCommon?filterBy=ALL&sortBy=RELATIONSHIP&page=1&matchTestGuid=861ABA15-2DEE-495B-A843-42166C59F80C
Takes username, password, and the number of pages of matches, returns list of
linked tests, then gathers match details and Shared Matches (ICW). Output is
in two csv files, ready for import into Gephi.
Networks are terribly unreliable. The script was crashing out after getting empty
replies. Trying out the requests_retry_session from here:
https://www.peterbe.com/plog/best-practice-with-retries-with-requests
""" 

import requests
import json
import getpass
import time
import os
import sys
import csv
import pprint
import datetime
import progressbar
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# URL data
login_url = "https://www.ancestry.com/account/signin"
prefix_url = "https://dnahomeaws.ancestry.com/dna/secure/tests/"
matches_url_suffix = "/matches?filterBy=ALL&sortBy=RELATIONSHIP&page="
shared_matches_url_suffix1 = "/matchesInCommon?filterBy=ALL&sortBy=RELATIONSHIP&page="
shared_matches_url_suffix2 = "&matchTestGuid="


def get_json(session, url):
    # Get the raw JSON for the tests
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'
    headers = {'User-Agent': user_agent}
    r = requests_retry_session(session).get(url, headers=headers)
    # debug
    # print("Raw encoding type:", r.encoding)
    if r.encoding == None:
        time.sleep(2)
        r = requests_retry_session(session).get(url, headers=headers)   
    raw = r.text
    # parse it into a dict
    data = json.loads(raw)
    return data


def requests_retry_session(session,
                           retries=3,
                           backoff_factor=0.3,
                           status_forcelist=(500, 502, 504)
    ):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_credentials():
    # Username and password should be provided by user via input
    username = input("Ancestry username: ")
    # This should be masked
    password = getpass.getpass(prompt='Ancestry Password: ', stream=None)
    return username, password


def get_guids(raw_data):
    tests = {}
    for i in range(len(raw_data['data']['completeTests'])):
        guid = (raw_data['data']['completeTests'][i]['guid'])
        tester = (raw_data['data']['completeTests'][i]['testSubject']
                  ['givenNames'] + " " + raw_data['data']['completeTests']
                  [i]['testSubject']['surname'])
        tests[i+1] = tester, guid
    return tests    


def get_max_pages():
    # Get max number of pages to scrape.
    print("""
There are about 50 matches per page. The default sorting lists closer
matches on the earlier pages. That means that the more pages scanned,
the more false positives will be brought in. Based on my results,
things start getting really sketchy around page 25 to 30. This is 1500
matches, which is more than I will ever be concerned about. Also, it
takes about 30 seconds per page of (50) matches. Sure, that sounds
fast with only a few pages, but if you try to grab "ALL" of your
matches (1000 pages max), you are talking several hours.
""")
    print("How many pages of matches would you like to capture?")
    user_max = input("Enter a number, or All for all pages: ")
    if user_max == "" or user_max.lower() == "all":
        user_max = "1000"
    user_max = int(user_max)
    print()
    print(user_max*50, "matches coming right up!")
    return user_max


def delete_old(prefix):
    # Delete old files
    print("Deleting old files")
    if os.path.exists(prefix+"edges.csv"):
        try:
            os.remove(prefix+"edges.csv")
        except PermissionError:
            print(prefix+"edges.csv is open.")
            input("Press any key after you close the file.")
    if os.path.exists(prefix+"nodes.csv"):
        try:
            os.remove(prefix+"nodes.csv")
        except PermissionError:
            print(prefix+"nodes.csv is open.")
            input("Press any key after you close the file.")


def make_data_file(prefix, type):
    filename = prefix + type
    if "nodes" in filename:
        header = ['Label', 'ID', 'Starred', 'Confidence',
                  'cMs', 'Segments', 'Notes']
    if "edges" in filename:
        header = ['Source', 'Target']
    with open(filename, "w", newline='') as f:
        data_file = csv.writer(f)
        data_file.writerow(header)
    return filename


def harvest_matches(session, data, guid, nodes_file, edges_file):
    for i in range(len(data['matchGroups'])):
        for m in range(len(data['matchGroups'][i]['matches'])):
            match_name = data['matchGroups'][i]['matches'][m]['matchTestDisplayName']
            match_guid = data['matchGroups'][i]['matches'][m]['testGuid']
            match_starred = data['matchGroups'][i]['matches'][m]['starred']
            match_confidence = data['matchGroups'][i]['matches'][m]['confidence']
            match_cms = data['matchGroups'][i]['matches'][m]['sharedCentimorgans']
            match_segments = data['matchGroups'][i]['matches'][m]['sharedSegments']
            match_notes = data['matchGroups'][i]['matches'][m]['note']
            match_starred = data['matchGroups'][i]['matches'][m]['starred']
            match_details = (match_name, match_guid, match_starred,
                             match_confidence, match_cms, match_segments,
                             match_notes)
            with open(nodes_file, "a", newline='') as n:
                nodes = csv.writer(n)
                nodes.writerow(match_details)
            # Get Shared Matches
            page = 1
            while page < 3:
                # Build shared matches URL
                sm_url = str(prefix_url + guid + shared_matches_url_suffix1
                             + str(page) + shared_matches_url_suffix2
                             + match_guid)
                # Does second page of matches exist?
                second_page = harvest_shared_matches(session, sm_url,
                                                     match_guid, edges_file)
                # Code smell. Rough logic to increment or break.
                if second_page and page < 3:
                    page = page + 1
                else:
                    page = 3


def harvest_shared_matches(session, sm_url, match_guid, edges_file):
    # Grab the ICW data first, and add it to edges.csv
    sm_data = get_json(session, sm_url)
    for mg in range(len(sm_data['matchGroups'])):
        for sm in range(len(sm_data['matchGroups'][mg]['matches'])):
            sm_guid = sm_data['matchGroups'][mg]['matches'][sm]['testGuid']
            icw = (match_guid, sm_guid)
            with open(edges_file, "a", newline='') as e:
                edges = csv.writer(e)
                edges.writerow(icw)
    # Then check for second page existance.
    if sm_data['pageCount'] == 1:
        return False
    else:
        return True


def main():
    # Login
    username, password = get_credentials()
    payload = {"username": username,
               "password": password}

    # Create session object
    session_requests = requests.session()

    # Start Session
    with session_requests as session:
        session.post(login_url, data=payload)
        data = get_json(session, prefix_url)

        # Get the list of tests available as a dict
        test_guids = get_guids(data)
        print()
        print("Available tests:")
        # Print them out...work on formatting
        for k, v in test_guids.items():
            """ k is the number associated with the test kit.
                v[0] is the test taker's name.
                v[1] is the guid for the test kit.
            """
            print("Test", str(k) + ":", v[0])
        test_selection = int(input("\nSelect the Test # that you want to gather \
matches for: "))
        test_taker = test_guids[test_selection][0].replace(' ', '')
        test_guid = test_guids[test_selection][1]

        # Get number of pages to retrieve
        max_pages = get_max_pages()

        # Deal with files
        filename_prefix = str(datetime.date.today()) + "_" + test_taker + "_"
        # Delete old files
        delete_old(filename_prefix)
        # Create new files
        nodes_file = make_data_file(filename_prefix, "nodes.csv")
        edges_file = make_data_file(filename_prefix, "edges.csv")
        
        # Start to gather match data using number of pages variable
        # Needs a test in here to see if there are as many pages as input.
        print("Gathering match details. Go do something productive.")
        for page_number in progressbar.progressbar(range(1, max_pages+1)):
            test_url = str(prefix_url + test_guid + matches_url_suffix
                           + str(page_number))
            matches = get_json(session, test_url)
            # print(len(matches['matchGroups']))
            if len(matches['matchGroups']) == 0:
                break
            else:
                harvest_matches(session, matches, test_guid, nodes_file, edges_file)
                time.sleep(1)
        print("\nMatch gathering complete.\n")


main()