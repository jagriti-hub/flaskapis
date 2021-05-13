from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json,requests
import kubernetes
from kubernetes import client, config

table_api = Blueprint('table_api', __name__)

def create_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,state_store,namespace,dbtype,tableid,Region):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        batch_v1 = client.BatchV1Api()
        volume2=client.V1Volume(
            name="kubeconfig",
            host_path={"path": kubeconfigpath}
        )
        mount2 = client.V1VolumeMount(
            name="kubeconfig",
            mount_path="/home/app/web/kubeconfig"
        )
        container = client.V1Container(
            name="tablejob"+tableid,
            image=tablejobimageid,
            volume_mounts=[mount2],
            command=["python","-u","app.py",table_path,dbid,tableid,Region],
            env=[{"name": "state_store","value":state_store}],
            image_pull_policy="Always"
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"tablejob": "tablejob"+tableid}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container],volumes=[volume2]))
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

def update_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,state_store,namespace,dbtype,tableid,Region):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        batch_v1 = client.BatchV1Api()
        volume2=client.V1Volume(
            name="kubeconfig",
            host_path={"path": kubeconfigpath}
        )
        mount2 = client.V1VolumeMount(
            name="kubeconfig",
            mount_path="/home/app/web/kubeconfig"
        )
        container = client.V1Container(
            name="tablejob"+tableid,
            image=tablejobimageid,
            volume_mounts=[mount2],
            command=["python","-u","update.py",table_path,dbid,tableid,Region],
            env=[{"name": "state_store","value":state_store}],
            image_pull_policy="Always"
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"tablejob": "tablejob"+tableid}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container],volumes=[volume2]))
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

def load_config_file(bucket_name, configfilepath):
  s3_client=boto3.client('s3')
  try:
    s3_response=s3_client.get_object(Bucket=bucket_name,Key=configfilepath)
    config_file_object=s3_response["Body"].read()
    config=json.loads(config_file_object)
    status="success"
    successmessage=configfilepath+" loaded Successfully"
    return("success", successmessage, config)
  except Exception as Error:
    status="error"
    errormessage=configfilepath+"not loaded Successfully"
    return(status, errormessage, Error)

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

@table_api.route('/live/v1/table', methods=['POST'])
def createtable():
    metadatas3url = os.getenv("imagemetaurl")
    kubeconfigpath = os.getenv("kubeconfigpath")
    state_store = os.getenv("state_store")
    tenantid = "servicedesigns"
    serviceid = request.json["serviceid"]
    dbtype = request.json["dbtype"]
    namespace = "default"
    dbid = request.json["dbid"]
    tableid = request.json["tableid"]
    Region = request.json["Region"]
    r=requests.get(metadatas3url)
    imagemetadata=r.json()
    jobregistryurl = imagemetadata['registryurl']+"/"
    print(imagemetadata)
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid
    table_configfile = table_path+"/config.json"
    if dbtype == "DYNAMODB":
        tableimagejobname = "dynamodbmockdeploy"
        tablejobimageid = jobregistryurl+imagemetadata['images'][tableimagejobname]['imagename']+":"+imagemetadata['images'][tableimagejobname]['tag'] 
    containerstatus,container_message,container_response=create_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,state_store,namespace,dbtype,tableid,Region)
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
    state_store = os.getenv("state_store")
    tenantid = "servicedesigns"
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid 
    table_outputfile=table_path+"/output.json"
    status,status_message,tableoutput_config=load_config_file(state_store,table_outputfile)
    if status == "error":
        successmessage={
            "error_message":"failed to load database outputfile",
            "status": 400
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
    state_store = os.getenv("state_store")
    tenantid = "servicedesigns"
    serviceid = request.json["serviceid"]
    dbid = request.json["dbid"]
    table_path=tenantid+"/"+serviceid+"/data/"+dbid+"/tables/"+ tableid
    table_logfile=table_path+"/log.json"
    status,status_message,tablelogs_config=load_config_file(state_store,table_logfile)
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

@table_api.route('/live/v1/table/<tableid>', methods=['DELETE'])
def deletetablejob(tableid):
    namespace = "default"
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
    return(status_message)

@table_api.route('/live/v1/table/update', methods=['POST'])
def updatetable():
    metadatas3url = os.getenv("imagemetaurl")
    kubeconfigpath = os.getenv("kubeconfigpath")
    state_store = os.getenv("state_store")
    tenantid = "servicedesigns"
    serviceid = request.json["serviceid"]
    dbtype = request.json["dbtype"]
    namespace = "default"
    dbid = request.json["dbid"]
    tableid = request.json["tableid"]
    Region = request.json["Region"]
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
    containerstatus,container_message,container_response=update_table_job(table_path,tablejobimageid,kubeconfigpath,dbid,state_store,namespace,dbtype,tableid,Region)
    successmessage={
        "status": "200",
        "containerstatus": containerstatus,
        "container_response": container_response
    }
    return(successmessage)
