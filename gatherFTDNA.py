import requests
import pprint
import csv
import os
import datetime
import getpass
import json
import time
import enlighten


cookies = {
    "_ga": "GA1.2.1681402700.1545789431",
    "ai_user": "HuWYR|2018-12-26T01:57:11.594Z",
    "ASP.NET_SessionId": "nyxuo23isnypku4zwvxbrtzd",
    "_gcl_au": "1.1.1817641569.1547761586",
    "_gid": "GA1.2.1634254588.1547761586",
    "_fbp": "fb.1.1547761585775.963271947",
    "__RequestVerificationToken": "4gkD8_TzKLf5Y3wIxoxd_OWlXsSLEDqsm4QcyAAgEf63QSmiyBG8Oyf9YB_JbR8E8j5tSoDLvq7ePULEr27SuzOGBqXiQmsRqB9TnqqDLglKcqR9byIqRVvFlSD5aSO7o6qf_XCgM1a7mcye-xcEAQ2",
    "BNI_ServerId": "0000000000000000000000001b960c0a00005000",
    "ai_session": "AKEnE|1547767829426|1547768364786.2",
}

headers = {
    "Origin": "https://www.familytreedna.com",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.familytreedna.com/sign-in",
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive",
    "Request-Id": "|Nthjy.b03Q0",
    "__RequestVerificationToken": "7AkM4a6cWkrg8pE_o6yXvnrJ2k_WRMVvG__oA1AXYFmRPLMTc3VuhvlvtYPb_5Xf4x_5Y0mITA34oh4M275TSCEkD9p7iGoV7TwWh-847c7SIBq7brNH1yFQTcnJLoXNEnGmCkpDwOdsSYT6wsZ8xw2",
    "Request-Context": "appId=cid-v1:8ec91be2-0790-49c2-aa80-f09f1e237de8",
}


def delete_old(prefix):
    # Delete old files
    print("Deleting old files")
    if os.path.exists(prefix + "_edges.csv"):
        try:
            os.remove(prefix + "_edges.csv")
        except PermissionError:
            print(prefix + "_edges.csv is open.")
            input("Press any key after you close the file.")
    if os.path.exists(prefix + "_nodes.csv"):
        try:
            os.remove(prefix + "_nodes.csv")
        except PermissionError:
            print(prefix + "_nodes.csv is open.")
            input("Press any key after you close the file.")



def get_login():
    test_taker = input("FTDNA Test Kit ID: ")
    psswrd = getpass.getpass("Password: ")
    amount = input("How many cousins would you like to collect? Enter All for all of them. ")
    return test_taker, psswrd, amount


def file_maker(test_taker):
    # Deal with files
    filename_prefix = str(datetime.date.today()) + "_FTDNA_" + test_taker
    # Delete old files
    delete_old(filename_prefix)
    node_filename = filename_prefix + "_nodes.csv"
    edge_filename = filename_prefix + "_edges.csv"
    return node_filename, edge_filename


def edge_build(edge_filename):
    with open(edge_filename, "w") as edges:
        edgeHeader = "Source,Target\n"
        edges.write(edgeHeader)


def build_data1(test_taker, psswrd):
    data1 = (
        '{"model":{"password":"'
        + psswrd
        + '","kitNum":"'
        + test_taker
        + '","rememberMe":false,"flow":""},"returnUrl":""}'
    )
    return data1


def build_data2(amount):
    #This gets built twice. The first time, amount is a small number. This is just so that we can
    #quickly determine the total number of cousins.
    #The second time through, we use the number entered by the user.
    data2 = '{"trial":0,"page":1,"pageSize":'+str(amount)+',"sortField":"relationshipPercentage()","sortDirection":"desc","filterId":0,"filterSince":null,"filter3rdParty":false,"filterEncryptedId":null,"searchName":null,"searchAncestral":null,"selectedBucket":0}'
    return data2


# Start
user, pwd, matches = get_login()
start = time.time()
node_file, edge_file = file_maker(user)
edge_build(edge_file)
data1 = build_data1(user, pwd)
data2 = build_data2(5)
session_requests = requests.session()

with requests.Session() as session:
    # Sign in
    post = session.post(
        "https://www.familytreedna.com/sign-in",
        headers=headers,
        cookies=cookies,
        data=data1,
    )
    # Get short cousin list
    short_response = session.post(
        "https://www.familytreedna.com/my/family-finder-api/matches",
        headers=headers,
        cookies=cookies,
        data=data2,
    )
    cousins = short_response.json()

    # Work on extracting total cousin count
    # print(cousins["count"])
    # go = input("press a button")
    if matches == "All" or matches == "all":
        count = int(cousins["count"])
    else:
        count = int(matches)
    print("Count is:",count)

    # Rebuild data2 based on total cousin count or user input    
    data2 = build_data2(count)

    # Get full cousin list
    response = session.post(
        "https://www.familytreedna.com/my/family-finder-api/matches",
        headers=headers,
        cookies=cookies,
        data=data2,
    )
    cousins = response.json()

    # Write cousin list to nodes.csv file
    with open(node_file, "a+", encoding="utf-8") as nodes:
        nodeHeader = "ID,Label,Email,Match Date,Total cM,Longest Block,Relationship Range,Suggested Relationship,Actual Relationship,YDNA,mtDNA,Notes,Ancestral\n"
        nodes.write(nodeHeader)
        pbar = enlighten.Counter(total=int(count), desc="Collecting cousin data", unit='cousins')
        # Next, extract cousin kitEncrypted value and loop
        for cousin in cousins["data"]:
            # print(cousin["name"])
            nodeLine = (
                str(cousin["resultId2"])
                + ","
                + cousin["name"].replace(",","-")
                + ","
                + cousin["email"].replace(",",";")
                + ","
                + str(cousin["rbDate"][:10])
                + ","
                + str(cousin["totalCM"])
                + ","
                + str(cousin["longestCentimorgans"])
                + ","
                + cousin["relationshipRange"].replace(",", "/ ")
                + ","
                + cousin["suggestedRelationship"].replace(",", "/ ")
                + ","
                + cousin["ftrRelationshipName"]
                + ","
                + cousin["yHaplo"]
                + ","
                + cousin["mtHaplo"]
                + ","
                + str(cousin["noteValue"]).replace("\n", " ").replace(",", " ")
                + ","
                + cousin["userSurnames"].replace(",", "_").replace("\"","")
                + "\n"
            )
            nodes.write(nodeLine)
            kitEnc = cousin["kitEncrypted"]
            # then request ICW like so:
            # https://www.familytreedna.com/my/family-finder-api/matches?page=1&pageSize=4000&filterEncryptedId=YmFzZTY0&filterId=5
            data4dict = {}
            data4dict.update({"filterId":5,"page":1,"pageSize":4000})
            data4dict.update({"filterencryptedid":kitEnc})
            data4 = str(data4dict)
            icwData = session.post(
                "https://www.familytreedna.com/my/family-finder-api/matches",
                headers=headers,
                cookies=cookies,
                data=data4,
            )
            try:
                icwList = icwData.json()
            except json.decoder.JSONDecodeError:
                pbar.update()
                continue

            #pprint.pprint(icwList)
            #with open("icwList.txt", "w") as iL:
            #    json.dump(icwList, iL)
            #go = input("press a button")
               
            # Write cousin["resultId2"] and icw["resultId2"] to nodes.csv
            with open(edge_file, "a+", encoding="utf-8") as edges:
                # Next, extract icw ID value and loop
                for icw in icwList["data"]:
                    edgeLine = (
                        str(cousin["resultId2"]) + "," + str(icw["resultId2"]) + "\n"
                    )
                    edges.write(edgeLine)
            pbar.update()

end = time.time()
print()
print("Complete.")
print(((end-start)/60)/60)

