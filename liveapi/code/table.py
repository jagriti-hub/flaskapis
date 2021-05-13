from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json,requests
import kubernetes
from kubernetes import client, config
import datafile

table_api = Blueprint('table_api', __name__)

def create_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,namespace,dbtype,tableid,Region,archeplaydatapath):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        batch_v1 = client.BatchV1Api()
        volume2=client.V1Volume(
            name="kubeconfig",
            host_path={"path": kubeconfigpath}
        )
        volume3=client.V1Volume(
            name="archeplaydata",
            host_path={"path": archeplaydatapath}
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
            name="tablejob"+tableid,
            image=tablejobimageid,
            volume_mounts=[mount2,mount3],
            command=["python","-u","app.py",table_path,dbid,tableid,Region],
            env=[{"name": "archeplaydatapath","value":"/home/app/web/archeplay/data"}],
            image_pull_policy="Always"
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"tablejob": "tablejob"+tableid}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container],volumes=[volume2,volume3]))
        # Create the specification of deployment
        spec = client.V1JobSpec(
            template=template,
            backoff_limit=0
        )
        # Instantiate the job object
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name="tablejob"+tableid),
            spec=spec)
        api_response = batch_v1.create_namespaced_job(
            body=job,
            namespace=namespace)
        success_message = tableid+" Deploy Job Intitated"
        return("success",success_message,str(api_response.status))
    except Exception as Error:
        error_message=tableid+" Failed to Intitate Deploy Job"
        return("error",error_message,str(Error))

def update_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,namespace,dbtype,tableid,Region,archeplaydatapath):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        batch_v1 = client.BatchV1Api()
        volume2=client.V1Volume(
            name="kubeconfig",
            host_path={"path": kubeconfigpath}
        )
        volume3=client.V1Volume(
            name="archeplaydata",
            host_path={"path": archeplaydatapath}
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
            name="tablejob"+tableid,
            image=tablejobimageid,
            volume_mounts=[mount2,mount3],
            command=["python","-u","update.py",table_path,dbid,tableid,Region],
            env=[{"name": "archeplaydatapath","value":archeplaydatapath}],
            image_pull_policy="Always"
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"tablejob": "tablejob"+tableid}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container],volumes=[volume2,volume3]))
        # Create the specification of deployment
        spec = client.V1JobSpec(
            template=template,
            backoff_limit=0
        )
        # Instantiate the job object
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name="tablejob"+tableid),
            spec=spec)
        api_response = batch_v1.create_namespaced_job(
            body=job,
            namespace=namespace)
        success_message = tableid+" Deploy Job Intitated"
        return("success",success_message,str(api_response.status))
    except Exception as Error:
        error_message=tableid+" Failed to Intitate Deploy Job"
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

def delete_job(tableid,namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance = client.BatchV1Api()
        api_response = api_instance.delete_namespaced_job(
            name='tablejob' + tableid,
            namespace=namespace
        )
        return("success",api_response.status)
    except Exception as e:
        return("Failed",str(e))

def delete_pod(namespace,labelstring):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance=client.CoreV1Api()
        podlist=api_instance.list_namespaced_pod(namespace, label_selector=labelstring)
        podname=podlist.items[0].metadata.name
        response=api_instance.delete_namespaced_pod(namespace=namespace,name=podname)
        return("success","Successfully_deleted_dbpod")
    except Exception as e:
        return("Failed",str(e))

def get_console_log(namespace,fieldstring):
    api_instance=client.CoreV1Api()
    name = fieldstring
    follow = True
    pretty = 'true'
    timestamps = True
    try:
        api_response = api_instance.read_namespaced_pod_log(name, namespace, follow=follow, pretty=pretty, timestamps=timestamps)
        console_log_status = "success"
        console_log_message = "Showing console Log"
        console_log = str(api_response)
        return(console_log_status,console_log_message,console_log)
    except Exception as e:
        console_log_status = "error"
        console_log_message = "Error Showing console Log"
        console_log = str(e)
        return(console_log_status,console_log_message,console_log)

@table_api.route('/live/v1/table', methods=['POST'])
def createtable():
    metadatas3url = os.getenv("imagemetaurl")
    kubeconfigpath = os.getenv("kubeconfigpath")
    archeplaydatapath = os.getenv("archeplaydatapath")
    tenantid = "servicedesigns"
    serviceid = request.json["serviceid"]
    dbtype = request.json["dbtype"]
    namespace = "default"
    dbid = request.json["dbid"]
    tableid = request.json["tableid"]
    Region = "us-east-1"
    r=requests.get(metadatas3url)
    imagemetadata=r.json()
    jobregistryurl = imagemetadata['registryurl']+"/"
    print(imagemetadata)
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid
    table_configfile = table_path+"/config.json"
    if dbtype == "DYNAMODB":
        tableimagejobname = "dynamodbmockdeploy"
        tablejobimageid = jobregistryurl+imagemetadata['images'][tableimagejobname]['imagename']+":"+imagemetadata['images'][tableimagejobname]['tag'] 
    containerstatus,container_message,container_response=create_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,namespace,dbtype,tableid,Region,archeplaydatapath)
    successmessage={
    "status": "200",
    "containerstatus": containerstatus,
    "container_response": container_response
    }
    return(successmessage)

@table_api.route('/live/v1/table/<tableid>', methods=['GET'])
def gettable(tableid):
	namespace = "default"
	fieldstring = 'metadata.name='+"tablejob"+tableid
	jobstatus,jobmessage = get_job_status(namespace,fieldstring)
	db_job_status_data={
		"jobstatus": jobstatus,
		"jobmessage": jobmessage,
		"tableid": tableid
	} 
	successmessage={
		"status": 200,
		"jobstatus_data": db_job_status_data
	}
	return(successmessage)

@table_api.route('/live/v1/<serviceid>/<dbid>/table/<tableid>/output', methods=['GET'])
def getoutput(tableid,serviceid,dbid):
    tenantid = "servicedesigns"
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid 
    table_outputfile=table_path+"/output.json"
    namespace = "default"
    fieldstring = 'metadata.name='+"tablejob"+tableid
    status,status_message,tableoutput_config=datafile.load_s3_file(table_outputfile)
    if status == "error":
        #check job
        jobstatus,jobmessage = get_job_status(namespace,fieldstring)
        if jobstatus == "Not Deployed":
            successmessage={
                "job_status":"Not Deployed",
                "status": 200
            }
        else:
            successmessage={
                "job_status":"Initiated",
                "status": 200,
            }
    else:
        table_output=tableoutput_config["state"]
        successmessage={
            "db_output": table_output,
            "status": 200
        }
    return(successmessage)

@table_api.route('/live/v1/<serviceid>/<dbid>/table/<tableid>/logs', methods=['GET'])
def getlogs(tableid,serviceid,dbid):
    tenantid = "servicedesigns"
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid
    table_logfile=table_path+"/log.json"
    status,status_message,tablelogs_config=datafile.load_s3_file(table_logfile)
    if status == "error":
        successmessage={
            "error_message":"failed to load database logfile",
            "status": 400
        }
    else:
        successmessage={
            "db_output": tablelogs_config,
            "status": 200
        }
    return(successmessage)

@table_api.route('/live/v1/<serviceid>/<dbid>/table/<tableid>', methods=['DELETE'])
def deletetablejob(serviceid,dbid,tableid):
    namespace = "default"
    labelstring = 'tablejob='+'tablejob'+tableid
    tenantid = "servicedesigns"
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid 
    table_outputfile=table_path+"/output.json"
    table_logfile=table_path+"/log.json"
    jobstatus,jobstatus_message=delete_job(tableid,namespace)
    podstatus,podstatus_message=delete_pod(namespace,labelstring)
    if jobstatus== "success":
        if podstatus == "success":
            delete_op_status,delete_op_status_message,delete_op_response=datafile.delete_s3_file(table_outputfile)
            delete_logs_status,delete_logs_status_message,delete_logs_response=datafile.delete_s3_file(table_logfile)
            if delete_op_status == "success" and delete_logs_status == "success":
                status_message={
                    "status": 200,
                    "status_message": "tablejob_and_pod_deleted_successfully"
                }
            else:
                status_message={
                    "status": 400,
                    "status_message": delete_op_status_message,
                    "error_message": delete_op_response
                }
        else:
            status_message={
                "status": 400,
                "status_message": "tablepod_deletion_failed",
                "error_message": podstatus_message
            }
    else:
        status_message={
            "status": 400,
            "status_message": "tablejob_deletion_failed",
            "error_message": jobstatus_message
        }
    return(status_message)

@table_api.route('/live/v1/table/update', methods=['POST'])
def updatetable():
    metadatas3url = os.getenv("imagemetaurl")
    kubeconfigpath = os.getenv("kubeconfigpath")
    archeplaydatapath = os.getenv("archeplaydatapath")
    tenantid = "servicedesigns"
    serviceid = request.json["serviceid"]
    dbtype = request.json["dbtype"]
    namespace = "default"
    dbid = request.json["dbid"]
    tableid = request.json["tableid"]
    Region = "us-east-1"
    labelstring = 'tablejob='+'tablejob'+tableid
    jobstatus,jobstatus_message=delete_job(tableid,namespace)
    podstatus,podstatus_message=delete_pod(namespace,labelstring)
    if jobstatus== "success":
        if podstatus == "success":
            status_message={
                "status": 200,
                "status_message": "tablejob_and_pod_deleted_successfully"
            }
        else:
            status_message={
                "status": 400,
                "status_message": "tablepod_deletion_failed",
                "error_message": podstatus_message
            }
    else:
        status_message={
            "status": 400,
            "status_message": "tablejob_deletion_failed",
            "error_message": jobstatus_message
        }
    r=requests.get(metadatas3url)
    imagemetadata=r.json()
    jobregistryurl = imagemetadata['registryurl']+"/"
    print(imagemetadata)
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid
    table_configfile = table_path+"/config.json"
    if dbtype == "DYNAMODB":
        tableimagejobname = "dynamodbmockdeploy"
        tablejobimageid = jobregistryurl+imagemetadata['images'][tableimagejobname]['imagename']+":"+imagemetadata['images'][tableimagejobname]['tag'] 
    time.sleep(5)
    containerstatus,container_message,container_response=update_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,namespace,dbtype,tableid,Region,archeplaydatapath)
    successmessage={
        "status": "200",
        "containerstatus": containerstatus,
        "container_response": container_response
    }
    return(successmessage)

@table_api.route('/live/v1/table/<serviceid>/<dbid>/table/<tableid>/consolelog', methods=['GET'])
def getconsolelogs(serviceid,tableid,versionid):
    table_path="servicedesigns/"+serviceid+"/data/"+dbid+"/tables/"+ tableid 
    table_console_logfile=table_path+"/consolelog.json"
    namespace = "default"
    fieldstring = 'metadata.name='+"tablejob"+tableid
    status,status_message,table_logs_config=datafile.load_s3_file(table_console_logfile)
    if status == "error":
        #check job
        jobstatus,jobmessage = get_job_status(namespace,fieldstring)
        if jobstatus == "Not Deployed":
            successmessage={
                "job_status":"Not Deployed",
                "status": 200
            }
        else:
            console_log_status,console_log_message,consolelog=get_console_log(namespace,fieldstring)
            if console_log_status == "success":
                successmessage={
                    "job_status":"Initiated",
                    "status": 200,
                    "consolelog": consolelog
                }
            else:
                successmessage={
                    "job_status":"Initiated",
                    "status": 200,
                    "consolelog": console_log_message,
                    "consolelogsample": consolelog
                }
    else:
        table_output=table_output_config["state"]
        console_log_status,console_log_message,consolelog=get_console_log(namespace,fieldstring)
        if console_log_status == "success":
            successmessage={
                "table_output": table_output,
                "status": 200,
                "consolelog": consolelog
            }
        else:
            successmessage={
                "table_output": table_output,
                "status": 200,
                "consolelog": console_log_message
            }
    return(successmessage)