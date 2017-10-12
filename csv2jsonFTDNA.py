#!/usr/bin/env python
"""This script takes in Match (node), ICW (edge), and ChromosomeBrowser (cb)
    files and smashes them all together into a json format, which is exported
    to nodes.json file."""

import csv
import os
import json
from tkinter import filedialog, Tk

# Create empty lists
nodeData = []
edgeData = []
cbData = []
nodeDict = {}

################################################################################

def which_directory():
    """This function provides an easy GUI for the user to select the
        working directory of the files.
    """
    # Ask for the directory to get the files from
    root = Tk().withdraw() # .withdraw() hides that second blank window
    # This sets to the users home directory
    init_dir = os.path.expanduser('~')
    # These options in .askdirectory seem to get the job done!
    filedirectory = filedialog.askdirectory(initialdir=init_dir,
                                            title='Please select a directory')
    return filedirectory

def csv2list(search_string):
    """(string) -> list

    This creates a basic list from a csv file and returns it.
    """
    for filename in os.listdir(file_directory):
        if search_string in filename:
            with open(os.path.join(file_directory, filename), 'r', encoding="UTF8") as ffile:
                freader = csv.reader(ffile)
                fdata = list(freader)
            return fdata

def make_nodeDict(node_Data):
    """(list) -> dict

    This function starts processing the match list and converts it into
    a dictionary of dictionaries.
    """
    # Read the column names from the first line of the file
    nodeFields = node_Data[0]
    # Fix ID column header
    if nodeFields[11] == "ResultID2":
        nodeFields[11] = nodeFields[11].replace("ResultID2", "ID")
    # Fix Label column header
    if nodeFields[13] == "Name":
        nodeFields[13] = nodeFields[13].replace("Name", "Label")
    # Make copy of nodeFields without ID.
    # This is in case we ever merge the cleanup script and this one.
    nodeSubFields = nodeFields
    del nodeSubFields[11]
    # Pop off first row (the headers)
    node_Data.pop(0) # Now we have Headers and nodes objects
    # Set counter to 0
    count = 0
    node_Dict = {}
    # Give types to the columns
    col_types = [str, str, str, str, float, float, int, str, str, str, str, str, str]
    # Start to cycle through nodes list
    for nodeRow in node_Data:
        nodeDictEntry = {}
        nodeID = nodeRow[11]
        # Remove ID index
        del nodeRow[11]
        # Break Ancestral string into Ancestral list
        nodeRow[8] = nodeRow[8].split('| ')
        # Apply types to columns
        nodeRow = tuple(convert(value) for convert, value in zip(col_types, nodeRow))
        # Zip together the field names and values to create Dictionary nodeDictEntry
        nodeDictEntry.update(dict(zip(nodeSubFields, nodeRow)))
        # Make icwList and append to nodeDictEntry
        nodeDictEntry.update({'ICW':makeICW(edgeData, nodeID)})
        # Make cbList and append to nodeDictEntry
        nodeDictEntry.update({'Chromosome Data':makeCB(cbData, nodeID)})
        node_Dict[nodeID] = nodeDictEntry
        os.system('cls')
        print("Nodes processed: ", count)
        count = count + 1
    return node_Dict

def makeICW(edge_Data, node_ID):
    """(list, string) -> smaller list

    Simple function to extract ICW data and convert to a List.
    This List is then added to the main nodeDict as a dictionary
    entry, ala {ICW:icwList}
    """
    icwList = []
    # Cycle through edgeData, created above from ICW file
    for edgeRow in edge_Data:
    # If Source column value = the nodeID...
        if edgeRow[5] == node_ID:
    # ...add the Target column value to icwList
            icwList.append(edgeRow[6])
    return icwList

def makeCB(cb_Data, nodeID):
    """(list, string) -> list of lists of dictionaries

    This function will get a little more complex than makeICW. Basically,
    it will take the cbData and create a list of lists of dictionary entries.
    This mess will then be appeneded to the main nodeDict as a dictionary entry,
    ala {ChromosomeData:cbList}
    """
    # create cbList
    cbList = []
    cb_List = []
    # Cycle through cb_Data, paring it down to just the data (remove names)
    for cbRow in cb_Data:
        cbList.append([cbRow[2], cbRow[3], cbRow[4],
                       cbRow[5], cbRow[6], cbRow[7]])
    # Read the column names from the first line of the file
    cbFields = cbList[0]
    # Pop off first row (the headers)
    cbList.pop(0) # Now we have Headers and cbs objects
    #cbDictEntry = {}
    # Give types to the columns
    col_types = [int, int, int, float, int]
    # Start to cycle through cbs list
    for cbListRow in cbList:
        cbDictEntry = {}
        # Grab the match Kit ID
        cbID = cbListRow[5]
        # Remove last column, the match Kit ID
        cbListRow.pop(5)
        # Apply types to columns
        cbListRow = tuple(convert(value) for convert, value in zip(col_types, cbListRow))
        # Make cbList and append to cbDictEntry
        if cbID == nodeID:
            # Zip together the field names and values to create Dictionary cbDictEntry
            cbDictEntry.update(dict(zip(cbFields, cbListRow)))
            cb_List.append(cbDictEntry)
    return cb_List

def dict2json(node_Dict):
    # Check if nodes.json file exists
    if os.path.exists(os.path.join(file_directory, 'nodes.json')):
        # if it does, delete it
        os.remove(os.path.join(file_directory, 'nodes.json'))
        print("Deleted old nodes.json file.")
    # Writing JSON data
    with open(os.path.join(file_directory, 'nodes.json'), 'w') as f:
        json.dump(node_Dict, f)
        print("nodes.json file created.")

################################################################

file_directory = which_directory()
edgeData = csv2list('ICW')
cbData = csv2list('Browser')
nodeData = csv2list('Matches')
nodeDict = make_nodeDict(nodeData)

print()
print("nodeDict length: ", len(nodeDict))

dict2json(nodeDict)
