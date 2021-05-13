from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json
import datafile
import zipfile
import requests
import glob
import subprocess
import shutil,glob
from shutil import copyfile
from shutil import copytree, ignore_patterns
from distutils.dir_util import copy_tree
from kubernetes import client, config

datapath=os.getenv("archedatapath")

publish_api = Blueprint('publish_api', __name__)

def getfiles(step,serviceid,gitpath):
    createscript="#!/bin/bash\n"
    deletescript="#!/bin/bash\n"
    updatescript="#!/bin/bash\n"
    for stepid in step["deploysteps"]["steporder"]:
        for task in step["deploysteps"][stepid]["tasks"]:
            directory_to_extract_to=datapath+"/deploy/"+serviceid+"/"+step["optionname"]+"/"+stepid+"/task"+str(task["taskno"])+"/"+task["taskname"]
            filepath = gitpath+"/"+task["filepath"]
            file_list=glob.glob(filepath+"/*",recursive=True)
            for file in file_list:
                destpath=directory_to_extract_to+"/"+file.split("/")[-1]
                directory = os.path.dirname(destpath)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                copyfile(file,destpath)
            with open(directory_to_extract_to+"/create.sh","rt") as fin:
                newfile=""
                for line in fin:
                    filereplace=line.replace("PATHPARAM","deploy/"+serviceid+"/"+step["optionname"]+"/"+stepid+"/task"+str(task["taskno"])+"/"+task["taskname"].lower())
                    newfile=newfile+filereplace
            os.remove(directory_to_extract_to+"/create.sh")
            with open(directory_to_extract_to+"/create.sh","wt") as fout:
                fout.write(newfile)
            with open(directory_to_extract_to+"/delete.sh","rt") as fin:
                newfile=""
                for line in fin:
                    filereplace=line.replace("PATHPARAM","deploy/"+serviceid+"/"+step["optionname"]+"/"+stepid+"/task"+str(task["taskno"])+"/"+task["taskname"].lower())
                    newfile=newfile+filereplace
            os.remove(directory_to_extract_to+"/delete.sh")
            with open(directory_to_extract_to+"/delete.sh","wt") as fout:
                fout.write(newfile)
            with open(directory_to_extract_to+"/update.sh","rt") as fin:
                newfile=""
                for line in fin:
                    filereplace=line.replace("PATHPARAM","deploy/"+serviceid+"/"+step["optionname"]+"/"+stepid+"/task"+str(task["taskno"])+"/"+task["taskname"].lower())
                    newfile=newfile+filereplace
            os.remove(directory_to_extract_to+"/update.sh")
            with open(directory_to_extract_to+"/update.sh","wt") as fout:
                fout.write(newfile)
            time.sleep(5)
            text_files = glob.glob(directory_to_extract_to+"/*", recursive = True)
            if directory_to_extract_to+"/inputoption.json" in text_files:
                f=open(directory_to_extract_to+"/inputoption.json","r")
                inputoption=f.read()
                jsoninput=json.loads(inputoption)
                task["input_options"]=jsoninput
                task["formfill"]=True
            else:
                task["input_options"]={}
                task["formfill"]=False
            taskpath="deploy/"+serviceid+"/"+step["optionname"]+"/"+stepid+"/task"+str(task["taskno"])+"/"+task["taskname"].lower()
            args=""
            for arg in task["Create"]["args"]:
                arg=arg.replace("SERVICEID",serviceid)
                args=args+" "+arg
            task["Create"]["Filename"]=task["Create"]["Filename"].replace("PATHPARAM",taskpath)
            task["createscript"]=task["Create"]["Type"]+" "+task["Create"]["Filename"]+" "+args
            createscript=createscript+task["createscript"]+"\n"
            args=""
            for arg in task["Delete"]["args"]:
                arg=arg.replace("SERVICEID",serviceid)
                args=args+" "+arg
            task["Delete"]["Filename"]=task["Delete"]["Filename"].replace("PATHPARAM",taskpath)
            task["deletescript"]=task["Delete"]["Type"]+" "+task["Delete"]["Filename"]+" "+args
            deletescript=deletescript+task["deletescript"]+"\n"
            args=""
            for arg in task["Update"]["args"]:
                arg=arg.replace("SERVICEID",serviceid)
                args=args+" "+arg
            task["Update"]["Filename"]=task["Update"]["Filename"].replace("PATHPARAM",taskpath)
            task["updatescript"]=task["Update"]["Type"]+" "+task["Update"]["Filename"]+" "+args
            updatescript=updatescript+task["updatescript"]+"\n"
    createshpath=datapath+"/deploy/"+serviceid+"/"+step["optionname"]+"/createscript.sh"
    with open(createshpath,"w") as f:
        f.write(createscript)
    deleteshpath=datapath+"/deploy/"+serviceid+"/"+step["optionname"]+"/deletescript.sh"
    with open(deleteshpath,"w") as f:
        f.write(deletescript)
    updateshpath=datapath+"/deploy/"+serviceid+"/"+step["optionname"]+"/updatescript.sh"
    with open(updateshpath,"w") as f:
        f.write(updatescript)
    return(step["deploysteps"])

def create_generator_job(kubeconfigpath,serviceid,namespace,archeplaydatapath,generatorpath):
  try:
    config.load_kube_config("/home/app/web/kubeconfig")
    batch_v1 = client.BatchV1Api()
    volume1=client.V1Volume(
      name="generatorjob"+serviceid,
      host_path={"path": "/var/run"}
    )
    volume2=client.V1Volume(
      name="kubeconfig",
      host_path={"path": kubeconfigpath}
    )
    volume3=client.V1Volume(
        name="archeplaydata",
        host_path={"path":archeplaydatapath}
    )
    mount1 = client.V1VolumeMount(
      name="generatorjob"+serviceid,
      mount_path="/var/run"
    )
    mount2 = client.V1VolumeMount(
      name="kubeconfig",
      mount_path="/home/app/web/kubeconfig"
    )
    mount3 = client.V1VolumeMount(
        name="archeplaydata",
        mount_path="/home/app/web/archeplay/data"
    )
    container = client.V1Container(
        name="generatorjob"+serviceid,
        image="python:3.8.1-slim-buster",
        volume_mounts=[mount1,mount2,mount3],
        command=["bash",generatorpath],
        image_pull_policy="Always"
    )
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"generatorjob": "generatorjob"+serviceid}),
        spec=client.V1PodSpec(restart_policy="Never", containers=[container],volumes=[volume1,volume2,volume3]))
    # Create the specification of deployment
    spec = client.V1JobSpec(
        template=template,
        backoff_limit=0
        )
    # Instantiate the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name="generatorjob"+serviceid),
        spec=spec)
    api_response = batch_v1.create_namespaced_job(
        body=job,
        namespace=namespace)
    success_message = "Generator Job Intitated"
    return("success",success_message,str(api_response.status))
  except Exception as Error:
    error_message="Generator job Failed to Intitate Deploy Job"
    return("error",error_message,str(Error))

def get_job_status(namespace,fieldstring):
    config.load_kube_config("/home/app/web/kubeconfig")
    api_instance=client.BatchV1Api()
    try:
        joblist=api_instance.list_namespaced_job(namespace,field_selector=fieldstring)
        print(str(joblist.items))
        try:
            if len(joblist.items) == 0:
                jobstatus = "Not Deployed"
                jobmessage= "Job is not deployed"
                return(jobstatus,jobmessage)
            jobname=joblist.items[0].metadata.name
            print(jobname)
            if joblist.items[0].status.active == 1:
                jobstatus = "inprogress"
                jobmessage= "Job "+jobname+" is inprogress"
            if joblist.items[0].status.active == None and joblist.items[0].status.succeeded == 1:
                jobstatus= "completed"
                jobmessage= "Job "+jobname+" is completed"
            elif joblist.items[0].status.active == None and joblist.items[0].status.failed == 1:
                jobstatus = "error"
                jobmessage = joblist.items[0].status
            return(jobstatus,str(jobmessage))
        except Exception as e:
            jobstatus = "error"
            jobmessage = str(e)
            return(jobstatus,jobmessage)
    except Exception as e:
        return("error",str(e))

@publish_api.route('/publish/v1/createdeploy/<productid>/<serviceid>', methods=['POST'])
def createdeploy(productid,serviceid):
    try:
        templatepath="/home/app/web/archeplay/template"
        servicepath= "services/"+productid+"/services.json"
        status,statusmessage,services=datafile.load_s3_file(servicepath)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage,"Error":services}
            return(message)
        for svc in services:
            if svc["serviceid"] == serviceid:
                servicetype=svc["servicetype"]
                svc["status"]="published"
        writestatus,writestatusmessage,srvswrite=datafile.write_s3_file(servicepath,services)
        if writestatus == "error":
            message={"statusCode":400,"errorMessage":writestatusmessage,"Error":srvswrite}
            return(message)
        svctemplatepath=templatepath+"/servicetemplates/"+servicetype+".json"
        with open(svctemplatepath,"r") as f:
            stepdata=f.read()
            stepjson=json.loads(stepdata)
        optionname=stepjson["optionname"]
        optionjson=getfiles(stepjson,serviceid,templatepath)
        optionpath="deploy/"+serviceid+"/"+optionname+"/"+optionname+".json"
        status,statusmessage,optionput=datafile.write_s3_file(optionpath,optionjson)
        if status == "success":
            message={"statusCode":200,"body":optionjson}
        else:
            message={"statusCode":400,"errorMessage":optionput}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@publish_api.route('/publish/v1/getoption/<serviceid>/<optionname>', methods=['GET'])
def getoption(serviceid,optionname):
    optionpath="deploy/"+serviceid+"/"+optionname+"/"+optionname+".json"
    status,statusmessage,optionjson=datafile.load_s3_file(optionpath)
    if status == "error":
        optionjson={}
    message={"statusCode":200,"body":optionjson}
    return(message)

@publish_api.route('/publish/v1/putinput/<optionname>', methods=['POST'])
def putinput(optionname):
    iop={
        "serviceid": "",
        "task":""
        }
    serviceid=request.json["serviceid"]
    task=request.json["task"]
    step=getoption(serviceid,optionname)
    stepjson=step["body"]
    try:
        for stepid in stepjson["steporder"]:
            for steptask in stepjson[stepid]["tasks"]:
                if steptask["taskname"]==task["taskname"]:
                    inputjson=task["input_options"]
                    steptask["input_options"]=inputjson
                    taskinputpath="deploy/"+serviceid+"/"+optionname+"/"+stepid+"/task"+str(task["taskno"])+"/"+stepid.lower()+"/inputoption.json"
                    status,statusmessage,taskwrite=datafile.write_s3_file(taskinputpath,inputjson)
                    if status == "error":
                        message={"statusCode":400,"errorMessage":statusmessage}
                        return(message)
                    task["formfill"]=False
                    steptask["formfill"]=False
        optionpath="deploy/"+serviceid+"/"+optionname+"/"+optionname+".json"
        status,statusmessage,stepput=datafile.write_s3_file(optionpath,stepjson)
        if status == "error":
            message={"statusCode":400,"errorMessage":statusmessage}
            return(message)
        message={"statusCode":200,"body":task}
        return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@publish_api.route('/publish/v1/generator/<serviceid>/<optionname>', methods=['POST'])
def generate(serviceid,optionname):
    try:
        kubeconfigpath = os.getenv("kubeconfigpath")
        archeplaydatapath = os.getenv("archeplaydatapath")
        namespace = "default"
        getoptionjson=getoption(serviceid,optionname)
        step=getoptionjson["body"]
        if step != {}:
            generatesh=""
            requirements=[]
            for stepid in step["steporder"]:
                for task in step[stepid]["tasks"]:
                    taskpath=datapath+"/deploy/"+serviceid+"/"+optionname+"/"+stepid+"/task"+str(task["taskno"])+"/"+task["taskname"].lower()
                    args=""
                    for arg in task["Generator"]["args"]:
                        arg=arg.replace("SERVICEID",serviceid)
                        arg=arg.replace("FILEPATH",taskpath)
                        args=args+" "+arg
                    task["Generator"]["Filename"]=task["Generator"]["Filename"].replace("PATHPARAM",taskpath)
                    generatesh=generatesh+task["Generator"]["Type"]+" "+task["Generator"]["Filename"]+" "+args+"\n"
                    for requirement in task["Generator"]["Requirements"]:
                        if requirement not in requirements:
                            requirements.append(requirement)
            pipcommand="pip install "
            for requirement in requirements:
                pipcommand=pipcommand+requirement+" "
            generatesh=pipcommand+"\n"+generatesh
            generateshpath=datapath+"/deploy/"+serviceid+"/"+optionname+"/generatescript.sh"
            with open(generateshpath,"w+") as f:
                f.write(generatesh)
            containerstatus,container_message,container_response=create_generator_job(kubeconfigpath,serviceid,namespace,archeplaydatapath,generateshpath)
            if containerstatus == "error":
                message={"statusCode":400,"errorMessage":container_message,"Error":container_response}
                return(message)
            message={"statusCode":200,"message":container_message}
            return(message)
        else:
            message={"statusCode":400,"errorMessage":"stepjson is empty"}
            return(message)
    except Exception as e:
        message={"statusCode":400,"errorMessage":str(e)}
        return(message)

@publish_api.route('/publish/v1/generator/<serviceid>', methods=['GET'])
def getgenerator(serviceid):
    namespace = "default"
    fieldstring = 'metadata.name='+"generatorjob"+serviceid
    jobstatus,jobmessage = get_job_status(namespace,fieldstring)
    resource_job_status_data={
        "jobstatus": jobstatus,
        "jobmessage": jobmessage,
        "serviceid": serviceid
    }
    successmessage={
        "status": 200,
        "body": resource_job_status_data
    }
    return(successmessage)
