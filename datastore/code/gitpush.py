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

git_api = Blueprint('git_api', __name__)

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

def create_branch(branch,branchnames,gitrepourl,archedesignpath,gitusername):
    try:
        if branch not in branchnames:
            repo = git.Repo.clone_from(gitrepourl,archedesignpath)
            giturl = repo.git
            giturl.checkout(b=branch)
            giturl.push('--set-upstream', 'origin', branch)
        elif branch in branchnames:
            try:
                repo = git.Repo.clone_from(gitrepourl,archedesignpath,branch=branch)
                giturl = repo.git
                repo.config_writer().set_value("user", "name", gitusername).release()
                repo.config_writer().set_value("user", "email", gitusername).release()
                giturl.pull('origin',branch,'--allow-unrelated-histories')
                destfolder="/home/app/web/archeplay/data"
                srcfolder=archedesignpath
                text_files = glob.glob(srcfolder+"/*",recursive=True)
                for filepath in text_files:
                    try:
                        destpath=destfolder+"/"+filepath.split("/")[-1]
                        copy_tree(filepath,destpath)
                    except:
                        pass
            except:
                repo = Repo(archedesignpath)
                giturl = repo.git
                repo.config_writer().set_value("user", "name", gitusername).release()
                repo.config_writer().set_value("user", "email", gitusername).release()
                giturl.pull('origin',branch,'--allow-unrelated-histories')
                destfolder="/home/app/web/archeplay/data"
                srcfolder=archedesignpath
                text_files = glob.glob(srcfolder+"/*",recursive=True)
                for filepath in text_files:
                    try:
                        destpath=destfolder+"/"+filepath.split("/")[-1]
                        copy_tree(filepath,destpath)
                    except:
                        pass
        message={"statusCode":200,"message":"branch created"}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

def shared_branch(branch,branchnames,gitrepourl,archedesignpath,gitusername):
    try:
        if branch not in branchnames:
            repo = git.Repo.clone_from(gitrepourl,archedesignpath)
            giturl = repo.git
            giturl.checkout(b=branch)
            giturl.push('--set-upstream', 'origin', branch)
        elif branch in branchnames:
            try:
                repo = git.Repo.clone_from(gitrepourl,archedesignpath,branch=branch)
                giturl = repo.git
                repo.config_writer().set_value("user", "name", gitusername).release()
                repo.config_writer().set_value("user", "email", gitusername).release()
                giturl.pull('origin',branch,'--allow-unrelated-histories')
            except:
                repo = Repo(archedesignpath)
                giturl = repo.git
                repo.config_writer().set_value("user", "name", gitusername).release()
                repo.config_writer().set_value("user", "email", gitusername).release()
                giturl.pull('origin',branch,'--allow-unrelated-histories')
        message={"statusCode":200,"message":"branch created"}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
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

def create_netrc():
    try:
        coderepoconfigpath="repoconfig/config.json"
        status,statusmessage,codecred=datafile.load_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage,"Error":codecred}
            return(message)
        gitrepourl=codecred["gitrepourl"]
        gitusername=codecred["gitusername"]
        gitpassword=codecred["gitpassword"]
        secretpath=os.getenv("NETRC")
        machine=gitrepourl.split("/")[2]
        gitcred="machine "+machine+" login "+gitusername+" password "+gitpassword+"\n"
        datawrite=writefile(secretpath,gitcred)
        destinationpath="/home/app/.netrc"
        directory = os.path.dirname(destinationpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copyfile(secretpath, destinationpath)
        return("success","netrc saved")
    except Exception as e:
        return("error",str(e))

def git_push(repopath,gitrepourl,gitbranch,gitusername,folder,commitmessage,tagname):
    try:
        status,statusmessage=create_netrc()
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        repo=Repo(repopath)
        giturl = repo.git
        try:
            origin = repo.create_remote('origin', url=gitrepourl,branch=gitbranch)
            assert origin.exists()
        except:
            pass
        repo.config_writer().set_value("user", "name", gitusername).release()
        repo.config_writer().set_value("user", "email", gitusername).release()
        repo.git.add(folder)
        repo.index.commit(commitmessage)
        repo.create_tag(tagname)
        giturl.push('--set-upstream','origin',gitbranch)
        return("success","pushed to git")
    except Exception as e:
        return("error",str(e))

@git_api.route('/datastore/v1/git', methods=['GET'])
def getcoderepo():
    coderepoconfigpath="repoconfig/config.json"
    status,statusmessage,coderepoconf=datafile.load_s3_file(coderepoconfigpath)
    if status == "error":
        coderepoconf={}
    message={"statusCode":200,"body":coderepoconf}
    return(message)

@git_api.route('/datastore/v1/git/validate', methods=['POST'])
def validate_cred():
    connectiontype=request.json["connectiontype"]
    gitrepourl=request.json["gitrepourl"]
    gitusername=request.json["gitusername"]
    gitpassword=request.json["gitpassword"]
    secretpath=os.getenv("NETRC")
    try:
        machine=gitrepourl.split("/")[2]
        gitcred="machine "+machine+" login "+gitusername+" password "+gitpassword+"\n"
        datawrite=writefile(secretpath,gitcred)
        destinationpath="/home/app/.netrc"
        directory = os.path.dirname(destinationpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copyfile(secretpath, destinationpath)
        archepath="/home/app/web/archeplay"
        localpath="/home/app/web/archeplay/"+uniqid("localgit")
        repo=git.Repo.clone_from(gitrepourl,localpath)
        branch=get_all_branches(localpath)
        a=branch.decode('ascii')
        liststr=list(a.split("\n"))
        liststr.remove('')
        branchnames=[]
        for name in liststr:
            branchname=name.split("/")
            branchnames.append(branchname[1])
        if branchnames == []:
            message={"statusCode":400,"message":"Default branch is not present please create a default branch"}
        else:
            message={"statusCode":200,"message":"giturl is authorized"}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":"giturl is unauthorized","Error":str(e)}
        return(message)

@git_api.route('/datastore/v1/git/credentials', methods=['POST'])
def store_cred():
    try:
        coderepoconfigpath="repoconfig/config.json"
        connectiontype=request.json["connectiontype"]
        gitrepourl=request.json["gitrepourl"]
        gitusername=request.json["gitusername"]
        gitpassword=request.json["gitpassword"]
        codecred={
            "connectiontype": connectiontype,
            "gitrepourl": gitrepourl,
            "gitusername": gitusername,
            "gitpassword": gitpassword,
            "mybranch": {},
            "sharedbranch": [],
            "environmentdeploybranch": []
        }
        machine=gitrepourl.split("/")[2]
        gitcred="machine "+machine+" login "+gitusername+" password "+gitpassword+"\n"
        status,statusmessage,coderepoconf=datafile.write_s3_file(coderepoconfigpath,codecred)
        if status == "error":
            message={"statusCode":400,"errorMessage":coderepoconf}
            return(message)
        secretpath=os.getenv("NETRC")
        datawrite=writefile(secretpath,gitcred)
        destinationpath="/home/app/.netrc"
        directory = os.path.dirname(destinationpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copyfile(secretpath, destinationpath)
        message={"statusCode":200,"message":"credentials added","body":codecred}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@git_api.route('/datastore/v1/git/getbranches', methods=['GET'])
def get_branches():
    try:
        coderepoconfigpath="repoconfig/config.json"
        status,statusmessage,codecred=datafile.load_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        gitrepourl=codecred["gitrepourl"]
        gitusername=codecred["gitusername"]
        archepath="/home/app/web/archeplay"
        localpath="/home/app/web/archeplay/"+uniqid("localgit")
        repo=git.Repo.clone_from(gitrepourl,localpath)
        repo.config_writer().set_value("user", "name", gitusername).release()
        repo.config_writer().set_value("user", "email", gitusername).release()
        branch=get_all_branches(localpath)
        a=branch.decode('ascii')
        liststr=list(a.split("\n"))
        liststr.remove('')
        branchnames=[]
        for name in liststr:
            branchname=name.split("/")
            branchnames.append(branchname[1])
        branchnames.pop(0)
        message={"statusCode":200,"body":branchnames}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@git_api.route('/datastore/v1/git/createbranches', methods=['POST'])
def create_branches():
    iop={
        "mybranch": {
            "Name": "",
            "Branchname": ""
        },
        "sharedbranch": [
            {
                "Name": "",
                "Branchname": ""
            },
            {
                "Name": "",
                "Branchname": ""
            }
        ],
        "environmentdeploybranch": [
            {
                "Name": "",
                "Branchname": ""
            },
            {
                "Name": "prod",
                "Branchname": ""
            }
        ]
    }
    try:
        branches=request.json["branches"]
        mybranch = branches["mybranch"]
        compsharedbranch=comparelistitems(branches["sharedbranch"])
        if compsharedbranch["statusCode"]==400:
            return(compsharedbranch)
        compenvbranch=comparelistitems(branches["environmentdeploybranch"])
        if compenvbranch["statusCode"]==400:
            return(compenvbranch)
        for sharedbranchitem in branches["sharedbranch"]:
            for envbranchitem in branches["environmentdeploybranch"]:
                if sharedbranchitem["Name"] == envbranchitem["Name"] or sharedbranchitem["Branchname"] == envbranchitem["Branchname"]:
                    message={"statusCode":400,"errorMessage": "Not unique name in environmentdeploybranch and sharedbranch"}
                    return(message)
        for sharedbranchitem in branches["sharedbranch"]:
            if sharedbranchitem["Name"] == mybranch["Name"] or sharedbranchitem["Branchname"] == mybranch["Branchname"]:
                message={"statusCode":400,"errorMessage": "Not unique name in mybranch and sharedbranch"}
                return(message)
        for envbranchitem in branches["environmentdeploybranch"]:
            if envbranchitem["Name"] == mybranch["Name"] or envbranchitem["Branchname"] == mybranch["Branchname"]:
                message={"statusCode":400,"errorMessage": "Not unique name in environmentdeploybranch and mybranch"}
                return(message)
        coderepoconfigpath="repoconfig/config.json"
        status,statusmessage,codecred=datafile.load_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        gitrepourl=codecred["gitrepourl"]
        gitusername=codecred["gitusername"]
        codecred["mybranch"]=branches["mybranch"]
        codecred["mybranch"]["Tags"]=[]
        codecred["sharedbranch"]=branches["sharedbranch"]
        codecred["environmentdeploybranch"]=branches["environmentdeploybranch"]
        secretpath=os.getenv("NETRC")
        destinationpath="/home/app/.netrc"
        directory = os.path.dirname(destinationpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copyfile(secretpath, destinationpath)
        writestatus,writestatusmessage,repoupdatebranch=datafile.write_s3_file(coderepoconfigpath,codecred)
        if writestatus == "error":
            message={"statusCode":400,"errorMessage":writestatusmessage}
            return(message)
        getbranch=get_branches()
        if getbranch["statusCode"] == 400:
            return(getbranch)
        branchnames=getbranch["body"]
        devdesignbranch=branches["mybranch"]["Branchname"]
        devdesignfoldername=branches["mybranch"]["Name"]
        archepath="/home/app/web/archeplay"
        archedesignpath=archepath+"/"+devdesignfoldername
        mybranchstatus=create_branch(devdesignbranch,branchnames,gitrepourl,archedesignpath,gitusername)
        if mybranchstatus["statusCode"] == 400:
            return(mybranchstatus)
        for sharedbranch in branches["sharedbranch"]:
            branch=sharedbranch["Branchname"]
            sharedfoldername=sharedbranch["Name"]
            folderpath=archepath+"/"+sharedfoldername
            sharedbranchstatus=shared_branch(branch,branchnames,gitrepourl,folderpath,gitusername)
            if sharedbranchstatus["statusCode"] == 400:
                return(sharedbranchstatus)
        for envbranch in branches["environmentdeploybranch"]:
            branch=envbranch["Branchname"]
            envfoldername=envbranch["Name"]
            folderpath=archepath+"/"+envfoldername
            envbranchstatus=create_branch(branch,branchnames,gitrepourl,folderpath,gitusername)
            if envbranchstatus["statusCode"] == 400:
                return(envbranchstatus)
        message={"statusCode":200,"body":codecred}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@git_api.route('/datastore/v1/git/getbranch/<branchtype>', methods=['GET'])
def get_branchbytype(branchtype):
    try:
        coderepoconfigpath="repoconfig/config.json"
        status,statusmessage,codecred=datafile.load_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        branches=codecred[branchtype]
        message={"statusCode":200,"body":branches}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@git_api.route('/datastore/v1/git/designpush', methods=['POST'])
def design_push():
    iop={
        "commitmessage":"",
        "tagname":""
    }
    try:
        coderepoconfigpath="repoconfig/config.json"
        status,statusmessage,codecred=datafile.load_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage,"Error":codecred}
            return(message)
        branch=codecred["mybranch"]["Branchname"]
        foldername=codecred["mybranch"]["Name"]
        gitrepourl=codecred["gitrepourl"]
        gitusername=codecred["gitusername"]
        commitmessage=request.json["commitmessage"]
        tagname=request.json["tagname"]
        srcfolder="/home/app/web/archeplay/data"
        destfolder="/home/app/web/archeplay/"+foldername
        copy_tree(srcfolder,destfolder)
        output_files = glob.glob(destfolder+"/**/*output.json", recursive = True)
        for file in output_files:
            os.remove(file)
        log_files = glob.glob(destfolder+"/**/*log.json", recursive = True)
        for file in log_files:
            os.remove(file)
        status,statusmessage=git_push(destfolder,gitrepourl,branch,gitusername,destfolder,commitmessage,tagname)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        codecred["mybranch"]["Tags"].append(tagname)
        writestatus,writestatusmessage,mybranchtag=datafile.write_s3_file(coderepoconfigpath,codecred)
        if writestatus == "error":
            message={"statusCode":400,"errorMessage":writestatusmessage}
            return(message)
        message={"statusCode":200,"message":statusmessage}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@git_api.route('/datastore/v1/git/designpush/<productid>/<serviceid>', methods=['POST'])
def shared_design_push(productid,serviceid):
    iop={
        "commitmessage":"",
        "Branchname": "",
        "Name": "",
        "SourceBranchName": "",
        "SourceName": "",
        "Tag": ""
    }
    try:
        commitmessage=request.json["commitmessage"]
        branch=request.json["Branchname"]
        foldername=request.json["Name"]
        sourcebranch=request.json["SourceBranchName"]
        sourcefoldername=request.json["SourceName"]
        Tag=request.json["Tag"]
        coderepoconfigpath="repoconfig/config.json"
        status,statusmessage,codecred=datafile.load_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage,"Error":codecred}
            return(message)
        gitrepourl=codecred["gitrepourl"]
        gitusername=codecred["gitusername"]

        ##pulling source tag
        localsorcepath="/home/app/web/archeplay/"+uniqid("localgit")
        repo=git.Repo.clone_from(gitrepourl,localsourcepath,branch=sourcebranch)
        repo.config_writer().set_value("user", "name", gitusername).release()
        repo.config_writer().set_value("user", "email", gitusername).release()
        giturl=repo.git
        giturl.pull('origin',sourcebranch,'--allow-unrelated-histories')
        giturl.checkout('tags/'+Tag)

        ###copying product json###
        productpath= localsourcepath+"/products/products.json"
        prodstatus,prodstatusmessage,products=datafile.load_copy_file(productpath)
        if prodstatus == "error":
            message={"statusCode":400,"errormessage":prodstatusmessage,"Error":products}
            return(message)
        copyproductpath="/home/app/web/archeplay/"+foldername+"/products/products.json"
        prodstatus,prodstatusmessage,copyproduct=datafile.load_copy_file(copyproductpath)
        if prodstatus == "error":
            copyproduct=[]
        for prod in products:
            if prod["productid"] == productid:
                copyproduct.append(prod)
        copyproductpath="/home/app/web/archeplay/"+foldername+"/products/products.json"
        prodstatus,prodstatusmessage,copyprod=datafile.write_copy_file(copyproductpath,copyproduct)
        if prodstatus == "error":
            message={"statusCode":400,"errorMessage":prodstatusmessage,"Error":copyprod}
            return(message)

        ###copying service json#####
        servicepath= localsourcepath+"/services/"+productid+"/services.json"
        srvstatus,srvstatusmessage,services=datafile.load_copy_file(servicepath)
        if srvstatus == "error":
            message={"statusCode":400,"errorMessage":srvstatusmessage,"Error":services}
            return(message)
        copyservicepath="/home/app/web/archeplay/"+foldername+"/services/"+productid+"/services.json"
        svcstatus,svcstatusmessage,copyservice=datafile.load_copy_file(copyservicepath)
        if svcstatus == "error":
            copyservice=[]
        for svc in services:
            if svc["serviceid"]==serviceid:
                copyservice.append(svc)
        copyservicepath="/home/app/web/archeplay/"+foldername+"/services/"+productid+"/services.json"
        svcstatus,svcstatusmessage,copysvc=datafile.write_copy_file(copyservicepath,copyservice)
        if svcstatus == "error":
            message={"statusCode":400,"errorMessage":svcstatusmessage,"Error":copysvc}
            return(message)
        
        ###copying design data###
        designdatapath=localsourcepath+"/servicedesigns/"+serviceid
        destfolder="/home/app/web/archeplay/"+foldername+"/servicedesigns/"+serviceid
        directory = os.path.dirname(destfolder)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copy_tree(designdatapath,destfolder)

        ###copying repoconfig####
        coderepoconfigpath=localsourcepath+"/repoconfig/config.json"
        destpath="/home/app/web/archeplay/"+foldername+"/repoconfig/config.json"
        directory = os.path.dirname(destpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copyfile(coderepoconfigpath,destpath)

        ###copying templateconfig####
        templaterepoconfigpath=localsourcepath+"/templateconfig/config.json"
        destpath="/home/app/web/archeplay/"+foldername+"/templateconfig/config.json"
        directory = os.path.dirname(destpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        copyfile(templaterepoconfigpath,destpath)

        ###pushing to git###
        pushfolder="/home/app/web/archeplay/"+foldername
        output_files = glob.glob(pushfolder+"/**/*output.json", recursive = True)
        for file in output_files:
            os.remove(file)
        log_files = glob.glob(pushfolder+"/**/*log.json", recursive = True)
        for file in log_files:
            os.remove(file)
        count=1
        push=True
        while push:
            tagname=serviceid+".v"+str(count)
            status,statusmessage=git_push(pushfolder,gitrepourl,branch,gitusername,pushfolder,commitmessage,tagname)
            if status == "success":
                for svc in services:
                    if svc["serviceid"]==serviceid:
                        svc["tagnames"].append(tagname)
                        svc["Branchname"]=branch
                        svc["Name"]=foldername
                srvstatus,srvstatusmessage,svcupdate=datafile.write_s3_file(servicepath,services)
                if srvstatus == "error":
                    message={"statusCode":400,"errorMessage":srvstatusmessage,"Error":svcupdate}
                    return(message)
                copysvcstatus,copysvcstatusmessage,copysvc=datafile.load_copy_file(copyservicepath)
                if copysvcstatus == "error":
                    message={"statusCode":400,"errormessage":copysvcstatusmessage}
                    return(message)
                for cpsvc in copysvc:
                    if cpsvc["serviceid"]==serviceid:
                        cpsvc["tagnames"].append(tagname)
                        cpsvc["Branchname"]=branch
                        cpsvc["Name"]=foldername
                writecpsvcstatus,writecpsvcstatusmessage,cpsrvice=datafile.write_copy_file(copyservicepath,copysvc)
                if writecpsvcstatus == "error":
                    message={"statusCode":400,"errorMessage":writecpsvcstatusmessage}
                    return(message)
                push=False
            else:
                if "already exists" in statusmessage:
                    count=count+1
                else:
                    message={"statusCode":400,"errorMessage":statusmessage}
                    return(message)
        message={"statusCode":200,"message":statusmessage}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@git_api.route('/datastore/v1/git/publish/<serviceid>/<optionname>', methods=['POST'])
def publish_push(serviceid,optionname):
    iop={
        "commitmessage":"",
        "Branchname": "",
        "Name": ""
    }
    try:
        commitmessage=request.json["commitmessage"]
        branch=request.json["Branchname"]
        foldername=request.json["Name"]
        coderepoconfigpath="repoconfig/config.json"
        status,statusmessage,codecred=datafile.load_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage,"Error":codecred}
            return(message)
        gitrepourl=codecred["gitrepourl"]
        gitusername=codecred["gitusername"]
        
        ###commands###
        pullcommand="git clone -b "+branch+" "+gitrepourl+" archedeploy\nexport CLONE_PATH=$PWD/archedeploy"
        optionpath="deploy/"+serviceid+"/"+optionname+"/"+optionname+".json"
        status,statusmessage,optionjson=datafile.load_s3_file(optionpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        createshcommand="bash "+"$CLONE_PATH/deploy/"+serviceid+"/"+optionname+"/createscript.sh"
        updateshcommand="bash "+"$CLONE_PATH/deploy/"+serviceid+"/"+optionname+"/updatescript.sh"
        deleteshcommand="bash "+"$CLONE_PATH/deploy/"+serviceid+"/"+optionname+"/deletescript.sh"
        finalstep={
            "deploy": {
                "description":"Run the command below to deploy resources",
                "tasks": [
                    {
                    "taskno": 1.0,
                    "description": "Clone Code repo",
                    "taskname": "Clone",
                    "initscript":pullcommand
                    },
                    {
                    "taskno": 2.0,
                    "description": "Deploy the resources",
                    "taskname": "Deploy",
                    "initscript":createshcommand
                    },
                    {
                    "taskno": 3.0,
                    "description": "Update the resources",
                    "taskname": "UpdateDeploy",
                    "initscript":updateshcommand
                    },
                    {
                    "taskno": 4.0,
                    "description": "Delete the resources",
                    "taskname": "Deletedeploy",
                    "initscript":deleteshcommand
                    }
                ]
            }
        }
        optionjson[optionname]=finalstep
        status,statusmessage,writeoptionjson=datafile.write_s3_file(optionpath,optionjson)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        
        ###pushing to git####
        srcfolder="/home/app/web/archeplay/data"
        destfolder="/home/app/web/archeplay/"+foldername
        pushfolder="deploy/*"
        copy_tree(srcfolder,destfolder)
        count=1
        push=True
        while push:
            tagname=serviceid+".v"+str(count)
            status,statusmessage=git_push(destfolder,gitrepourl,branch,gitusername,pushfolder,commitmessage,tagname)
            if status == "success":
                push=False
            else:
                if "already exists" in statusmessage:
                    count=count+1
                else:
                    message={"statusCode":400,"errorMessage":statusmessage}
                    return(message)
        message={"statusCode":200,"body":optionjson}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)


@git_api.route('/datastore/v1/git/deleteconf', methods=['DELETE'])
def deleteconf():
    try:
        coderepoconfigpath="repoconfig/config.json"
        secretpath=os.getenv("NETRC")
        netrcpath="/home/app/.netrc"
        status,statusmessage,delgitconf=datafile.delete_s3_file(coderepoconfigpath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        if os.path.exists(secretpath):
            os.remove(secretpath)
        if os.path.exists(netrcpath):
            os.remove(netrcpath)
        message={"statusCode":200,"message":"gitconfig deleted"}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errormessage":str(e)}
        return(message)