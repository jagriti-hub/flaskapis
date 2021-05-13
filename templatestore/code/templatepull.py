from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import os,json,sys
import time,math,random
import datafile
import git
from git import Repo
import subprocess
import shutil,glob
from shutil import copyfile
from shutil import copytree, ignore_patterns
from distutils.dir_util import copy_tree
datapath=os.getenv("archedatapath")

template_api = Blueprint('template_api', __name__)

def template_clone(gitrepourl,branch,folderpath,archetemplatepath,gitusername):
    try:
        try:
            repo = git.Repo.clone_from(gitrepourl,archetemplatepath,branch=branch)
            repo.config_writer().set_value("user", "name", gitusername).release()
            repo.config_writer().set_value("user", "email", gitusername).release()
            giturl = repo.git
            giturl.pull('origin',branch,'--allow-unrelated-histories')
            destfolder=folderpath
            srcfolder=archetemplatepath
            text_files = glob.glob(srcfolder+"/*",recursive=True)
            for filepath in text_files:
                try:
                    destpath=destfolder+"/"+filepath.split("/")[-1]
                    copy_tree(filepath,destpath)
                except:
                    pass
        except:
            repo = Repo(archetemplatepath)
            repo.config_writer().set_value("user", "name", gitusername).release()
            repo.config_writer().set_value("user", "email", gitusername).release()
            giturl = repo.git
            giturl.pull('origin',branch,'--allow-unrelated-histories')
            destfolder=folderpath
            srcfolder=archetemplatepath
            text_files = glob.glob(srcfolder+"/*",recursive=True)
            for filepath in text_files:
                try:
                    destpath=destfolder+"/"+filepath.split("/")[-1]
                    copy_tree(filepath,destpath)
                except:
                    pass
        return("success","template cloned")
    except Exception as e:
        return("error",str(e))

def get_all_branches(path):
    cmd = ['git', '-C', path, 'branch', '-r']
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out

def comparelistitems(items):
    count1=1
    count2=1
    for item1 in items:
        for item2 in items:
            if count1 != count2:
                if item1["Name"] == item2["Name"] or item1["Branchname"] == item2["Branchname"]:
                    message={"statusCode":400,"errorMessage": "Not unique name within "+items}
                    return(message)
            if count2 >= len(items):
                count2 = 0
            count2 = count2 + 1
        if count1 > len(items):
            break
        count1 = count1 +1
    message={"statusCode": 200, "message": "items are unique"}
    return(message)

def uniqid(prefix):
    m = time.time()
    sec = math.floor(m)
    ran = random.randint(0,96764685)
    usec = math.floor(ran * (m - sec))
    a= usec+sec
    x = '%3x' % (a)
    l = list(x)
    random.shuffle(l)
    y = ''.join(l)
    uniqid = prefix+y
    return uniqid

def writefile(datawritepath,gitcred):
    try:
        directory = os.path.dirname(datawritepath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        try:
            data_folder=open(datawritepath,"r+")
            data_string=data_folder.read()
            if gitcred not in data_string:
                data_folder.write(gitcred)
        except:
            data_folder=open(datawritepath,"w+")
            data_folder.write(gitcred)
        message={"statusCode":200,"message":"file written"}
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
    return(message)


@template_api.route('/templatestore/v1/git/templatepull', methods=['POST'])
def template_pull():
    iop={
        "connectiontype": "",
        "templategiturl": "",
        "templategitpassword":"",
        "templategitusername": "",
        "templategitbranch": ""
    }
    connectiontype=request.json["connectiontype"]
    templategiturl=request.json["templategiturl"]
    templategitpassword=request.json["templategitpassword"]
    templategitusername=t=request.json["templategitusername"]
    branch=request.json["templategitbranch"]
    try:
        machine=templategiturl.split("/")[2]
        gitcred="machine "+machine+" login "+templategitusername+" password "+templategitpassword+"\n"
        secretpath=os.getenv("NETRC")
        datawrite=writefile(secretpath,gitcred)
        destinationpath="/home/app/.netrc"
        directory = os.path.dirname(destinationpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copyfile(secretpath, destinationpath)
        folderpath="/home/app/web/archeplay/template"
        archetemplatepath="/home/app/web/archeplay/"+uniqid("localtemplate")
        status,statusmessage=template_clone(templategiturl,branch,folderpath,archetemplatepath,templategitusername)
        if status == "error":
            message={"statusCode":400,"errormessage": statusmessage}
            return(message)
        templatecred={
            "connectiontype": connectiontype,
            "templategiturl": templategiturl,
            "templategitpassword": templategitpassword,
            "templategitusername": templategitusername,
            "templategitbranch": branch
        }
        templaterepoconfigpath="templateconfig/config.json"
        status,statusmessage,templaterepoconf=datafile.write_s3_file(templaterepoconfigpath,templatecred)
        if status == "error":
            message={"statusCode":400,"errorMessage":"write error"}
            return(message)
        message={"statusCode":200,"message":"template git cloned"}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":"final error"}
        return(message)

@template_api.route('/templatestore/v1/git/templaterepo', methods=['GET'])
def gettemplaterepo():
    templaterepoconfigpath="templateconfig/config.json"
    status,statusmessage,templaterepoconf=datafile.load_s3_file(templaterepoconfigpath)
    if status == "error":
        templaterepoconf={}
    message={"statusCode":200,"body":templaterepoconf}
    return(message)


@template_api.route('/templatestore/v1/git/deleteconf', methods=['DELETE'])
def deleteconf():
    try:
        templaterepoconfigpath="templateconfig/config.json"
        secretpath=os.getenv("NETRC")
        netrcpath="/home/app/.netrc"
        status,statusmessage,delgitconf=datafile.delete_s3_file(templaterepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        if os.path.exists(secretpath):
            os.remove(secretpath)
        if os.path.exists(netrcpath):
            os.remove(netrcpath)
        message={"statusCode":200,"message":"templateconfig deleted"}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errormessage":str(e)}
        return(message)