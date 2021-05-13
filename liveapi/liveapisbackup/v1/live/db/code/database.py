from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json,requests
import kubernetes
from kubernetes import client, config

database_api = Blueprint('database_api', __name__)

def create_database_job(db_path,dbjobimageid,kubeconfigpath,dbid,state_store,namespace,dbtype):
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
            name="dbjob"+dbid,
            image=dbjobimageid,
            volume_mounts=[mount2],
            command=["python","-u","app.py",db_path,dbid,dbtype],
            env=[{"name": "state_store","value":state_store}],
            image_pull_policy="Always"
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"dbjob": "dbjob"+dbid}),
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
            metadata=client.V1ObjectMeta(name="dbjob"+dbid),
            spec=spec)
        api_response = batch_v1.create_namespaced_job(
            body=job,
            namespace=namespace)
        success_message = dbid+" Deploy Job Intitated"
        return("success",success_message,str(api_response.status))
    except Exception as Error:
        error_message=dbid+" Failed to Intitate Deploy Job"
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

def delete_deployment(dbid,namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance = client.AppsV1Api()
        api_response = api_instance.delete_namespaced_deployment(
            namespace = namespace,
            name= dbid
        )
        return("success",api_response.status)
    except Exception as e:
        return("Failed",str(e))

def delete_service(dbid,namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance=client.CoreV1Api()
        api_response = api_instance.delete_namespaced_service(
            namespace = namespace,
            name= dbid
        )
        return("success",api_response.status)
    except Exception as e:
        return("Failed",str(e))

def delete_job(dbid,namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance = client.BatchV1Api()
        api_response = api_instance.delete_namespaced_job(
            name='dbjob' + dbid,
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


@database_api.route('/live/v1/db', methods=['POST'])
def createdb():
    metadatas3url = os.getenv("imagemetaurl")
    kubeconfigpath = os.getenv("kubeconfigpath")
    state_store = os.getenv("state_store")
    tenantid = "servicedesigns"
    serviceid = request.json["serviceid"]
    dbtype = request.json["dbtype"]
    namespace = "default"
    dbid = request.json["dbid"]
    r=requests.get(metadatas3url)
    imagemetadata=r.json()
    jobregistryurl = imagemetadata['registryurl']+"/"
    print(imagemetadata)
    db_path=tenantid+"/"+serviceid+"/data/"+dbid
    db_configfile = db_path+"/config.json"
    if dbtype == "DYNAMODB":
        dbimagejobname = "dynamodb-database-deploy"
        dbjobimageid = jobregistryurl+imagemetadata['images'][dbimagejobname]['imagename']+":"+imagemetadata['images'][dbimagejobname]['tag'] 
    containerstatus,container_message,container_response=create_database_job(db_path,dbjobimageid,kubeconfigpath,dbid,state_store,namespace,dbtype)
    successmessage={
    "status": "200",
    "containerstatus": containerstatus,
    "container_response": container_response
    }
    return(successmessage)

@database_api.route('/live/v1/db/<dbid>', methods=['GET'])
def getdb(dbid):
	namespace = "default"
	fieldstring = 'metadata.name='+"dbjob"+dbid
	jobstatus,jobmessage = get_job_status(namespace,fieldstring)
	db_job_status_data={
		"jobstatus": jobstatus,
		"jobmessage": jobmessage,
		"dbid": dbid
	} 
	successmessage={
		"status": 200,
		"jobstatus_data": db_job_status_data
	}
	return(successmessage)

@database_api.route('/live/v1/<serviceid>/db/<dbid>/output', methods=['GET'])
def getoutput(dbid,serviceid):
    state_store = os.getenv("state_store")
    tenantid = "servicedesigns"
    db_path=tenantid+"/"+serviceid+"/data/"+dbid 
    db_outputfile=db_path+"/output.json"
    status,status_message,dboutput_config=load_config_file(state_store,db_outputfile)
    if status == "error":
        successmessage={
            "error_message":"failed to load database outputfile",
            "status": 400
        }
    else:
        db_output=dboutput_config["state"]
        successmessage={
            "db_output": db_output,
            "status": 200
        }
    return(successmessage)

@database_api.route('/live/v1/<serviceid>/db/<dbid>/logs', methods=['GET'])
def getlogs(dbid,serviceid):
    state_store = os.getenv("state_store")
    tenantid = "servicedesigns"
    db_path=tenantid+"/"+serviceid+"/data/"+dbid 
    db_logfile=db_path+"/log.json"
    status,status_message,dblogs_config=load_config_file(state_store,db_logfile)
    if status == "error":
        successmessage={
            "error_message":"failed to load database logfile",
            "status": 400
        }
    else:
        successmessage={
            "db_output": dblogs_config,
            "status": 200
        }
    return(successmessage)

@database_api.route('/live/v1/db/<dbid>', methods=['DELETE'])
def deletedb(dbid):
    namespace="default"
    labelstring = 'dbjob='+'dbjob'+dbid
    deployment_status,deployment_status_message=delete_deployment(dbid,namespace)
    service_status,service_status_message=delete_service(dbid,namespace)
    job_status,job_status_message=delete_job(dbid,namespace)
    pod_status,pod_status_message=delete_pod(namespace,labelstring)
    if deployment_status == "success":
        if service_status == "success":
            if job_status == "success":
                if pod_status == "success":
                    status_message={
                        "status": 200,
                        "status_message": "db_deleted_successfully"
                    }
                else:
                    status_message={
                        "status": 400,
                        "status_message": "dbpod_deletion_failed",
                        "error_message": pod_status_message
                    }
            else:
                status_message={
                    "status": 400,
                    "status_message": "dbjob_deletion_failed",
                    "error_message": job_status_message
                }
        else:
            status_message={
                    "status": 400,
                    "status_message": "dbservice_deletion_failed",
                    "error_message": service_status_message
                }
    else:
        status_message={
            "status": 400,
            "status_message": "dbdeployment_deletion_failed",
            "error_message": deployment_status
        }
    return(status_message)


