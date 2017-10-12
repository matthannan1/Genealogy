import csv
import sys
import os
from tkinter import filedialog, Tk
import tkinter
#import tkFileDialog


def which_directory():
    """This function provides an easy GUI for the user to select the
        working directory of the files."""
    # Ask for the directory to get the files from
    root = Tk().withdraw() # .withdraw() hides that second blank window
    # This sets to the users home directory
    init_dir = os.path.expanduser('~')
    # These options in .askdirectory seem to get the job done!
    filedirectory = filedialog.askdirectory(initialdir=init_dir,
                                            title='Please select a directory')
    return filedirectory

def makeNodes(anonymized):
    # Cleanup Family Finder Matches file and create nodes.csv
    # GUI file picker
    #print("Select Family Finder Matches file...")
    #initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*"))
    #filePath = tkFileDialog.askopenfilename(initialdir = "C:\Users\hannamj\Dropbox\Public\genealogy\$FamilyTree_GED\Gephi",
    #                                        title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))
    for filename in os.listdir(file_directory):
        if 'Matches' in filename:
            with open(os.path.join(file_directory, filename), 'r', encoding="UTF8") as ffile:
                # Create empty nodes list
                nodes = []
                readnodes = csv.reader(ffile)
                # Pump file contents into nodes list
                for row in readnodes:
                    nodes.append(row)
                # Read the column names from the first line of the file
                nodeHeader = nodes[0]
                # Fix ID column header
                if nodeHeader[11] == "ResultID2":
                    nodeHeader[11] = nodeHeader[11].replace("ResultID2", "ID")
                    print("Fixed ID Header")
                else:
                    print("ID Header OK")
                # Fix Label column header
                if nodeHeader[13] == "Name":
                    nodeHeader[13] = nodeHeader[13].replace("Name", "Label")
                    print("Fixed Label Header")
                else:
                    print("Label Header OK")
                # Pop off first row (the headers)
                nodes.pop(0)
                # Now we have Headers and nodes objects
            # Figure out working directory
            #workPath = os.path(file_directory)
            if anonymized == "y":
                nodeFile = str(file_directory + '/nodesAnonymized.csv')
            else:
                nodeFile = str(file_directory + '/nodes.csv')    
            print("DEBUG- ",nodeFile)
            # If nodes.csv exists, delete it
            if os.path.isfile(nodeFile):
                try:
                    os.unlink(nodeFile)
                    print("Removed previous nodes.csv file.")
                except:
                    print("No previous nodes.csv file found.")
            # Generate file based on Anonymized data or not
            if anonymized == "y":
                # Write the Header and nodes to file
                with open(nodeFile, 'wb+') as outfile:
                    writenodes = csv.writer(outfile)
                    writenodes.writerow([nodeHeader[1], nodeHeader[2], nodeHeader[3], nodeHeader[4],
                                        nodeHeader[5], nodeHeader[6], nodeHeader[8], nodeHeader[9],
                                        nodeHeader[10], nodeHeader[11], nodeHeader[12],nodeHeader[13]])
                    for row in nodes:
                        writenodes.writerow([row[1], row[2], row[3], row[4],
                                        row[5], row[6], row[8], row[9],
                                        row[10], row[11], row[12],row[11]])
            else:
                with open(nodeFile, 'wb+') as outfile:
                    writenodes = csv.writer(outfile)
                    writenodes.writerow([nodeHeader[0], nodeHeader[1], nodeHeader[2], nodeHeader[3], nodeHeader[4],
                                        nodeHeader[5], nodeHeader[6], nodeHeader[7], nodeHeader[8], nodeHeader[9],
                                        nodeHeader[10], nodeHeader[11], nodeHeader[12],nodeHeader[13]])
                    for row in nodes:
                        writenodes.writerow([row[0], row[1], row[2], row[3], row[4],
                                            row[5], row[6], row[7], row[8], row[9],
                                            row[10], row[11], row[12],row[13]])
            print("Created nodes.csv file")

def makeEdges():
    # Cleanup ICW file and create edges.csv
    # GUI file picker
    #print("Select ICW file...")
    #filePath = tkFileDialog.askopenfilename(initialdir = "C:\Users\hannamj\Dropbox\Public\genealogy\$FamilyTree_GED\Gephi",
    #                                        title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))

    for filename in os.listdir(file_directory):
        if 'ICW' in filename:
            with open(os.path.join(file_directory, filename), 'r', encoding="UTF8") as ffile:
                # Create empty edges list
                edges = []
                # Open the file
                with open(ffile, 'rb') as infile:
                    readedges = csv.reader(infile)
                # Pump file contents into edges list
                    for row in readedges:
                        edges.append(row)
                # Read the column names from the first line of the file
                    edgesHeader = edges[0]
                # Fix ID column header
                    if edgesHeader[5] == "Profile KitID":
                        edgesHeader[5] = edgesHeader[5].replace("Profile KitID", "Source")
                        print("Fixed Source Header")
                    else:
                        print("Source Header OK")
                # Fix Label column header
                    if edgesHeader[6] == "Match KitID":
                        edgesHeader[6] = edgesHeader[6].replace("Match KitID", "Target")
                        print("Fixed Target Header")
                    else:
                        print("Target Header OK")
                # Pop off first row (the headers)
                    edges.pop(0)
                # Now we have Headers and nodes objects

                # Build edgeFile
                #workPath = os.path(file_directory)
                edgeFile = str(file_directory + '/edges.csv')
                # If edges.csv exists, delete it
                if os.path.isfile(edgeFile):
                    try:
                        os.unlink(edgeFile)
                        print("Removed previous edges.csv file.")
                    except:
                        print("No previous edges.csv file found.")
                # Write the Header and nodes to file
                with open(edgeFile, 'wb+') as outfile:
                    writeedges = csv.writer(outfile)
                    writeedges.writerow([edgesHeader[5], edgesHeader[6]])
                    for row in edges:
                        writeedges.writerow([row[5], row[6]])
                print("Created edges.csv file")


print("Let's clean some data!")
print("What directory holds your files?")
file_directory = which_directory()
print("We'll start with Family Finder Match data")
userInput = input("Make data anonymized? (y/n)  ")
makeNodes(userInput)
print("Great! Now let's prep the ICW data")
makeEdges()
print("OK. That should do it.")
