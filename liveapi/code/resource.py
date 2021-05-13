import sys,os,boto3,time,math,random
import logging,json,requests
import docker
import kubernetes
from datetime import datetime
from flask import Flask, jsonify
from flask import Blueprint
from flask import request
from kubernetes import client, config

import datafile

resource_api = Blueprint('resource_api', __name__)

def delete_deployment(resourceid,namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance = client.AppsV1Api()
        api_response = api_instance.delete_namespaced_deployment(
            namespace = namespace,
            name= resourceid
        )
        return("success",api_response.status)
    except Exception as e:
        return("Failed",str(e))

def delete_service(resourceid,namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance=client.CoreV1Api()
        api_response = api_instance.delete_namespaced_service(
            namespace = namespace,
            name= resourceid
        )
        return("success",api_response.status)
    except Exception as e:
        return("Failed",str(e))

def delete_job(resourceid,namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance = client.BatchV1Api()
        api_response = api_instance.delete_namespaced_job(
            name='resourcejob' + resourceid,
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
        return("success","Successfully_deleted_resource_pod")
    except Exception as error:
        return("Failed",str(error))

def delete_ingress(name, namespace):
    try:
        config.load_kube_config("/home/app/web/kubeconfig")
        api_instance = client.NetworkingV1beta1Api()
        api_response = api_instance.delete_namespaced_ingress(name, namespace)
        return("success", "Ingress_deleted")
    except Exception as error:
        return("Failed",str(error))

def create_resource_job(resource_path,resourcejobimageid,kubeconfigpath,resourceid,code_type,serviceid,versionid,versionname,namespace,archeplaydatapath):
  try:
    config.load_kube_config("/home/app/web/kubeconfig")
    batch_v1 = client.BatchV1Api()
    volume1=client.V1Volume(
      name="buildjob"+resourceid,
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
      name="buildjob"+resourceid,
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
        name="resourcejob"+resourceid,
        image=resourcejobimageid,
        volume_mounts=[mount1,mount2,mount3],
        command=["python3","-u","app.py",serviceid,versionid,resourceid,versionname,namespace],
        env=[{"name": "archeplaydatapath","value":"/home/app/web/archeplay/data"}],
        image_pull_policy="Always"
    )
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"resourcejob": "resourcejob"+resourceid}),
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
        metadata=client.V1ObjectMeta(name="resourcejob"+resourceid),
        spec=spec)
    api_response = batch_v1.create_namespaced_job(
        body=job,
        namespace=namespace)
    success_message = resourceid+" Deploy Job Intitated"
    return("success",success_message,str(api_response.status))
  except Exception as Error:
    error_message=resourceid+" Failed to Intitate Deploy Job"
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

@resource_api.route('/live/v1/resource', methods=['POST'])
def createresource():
  metadatas3url = os.getenv("imagemetaurl")
  kubeconfigpath = os.getenv("kubeconfigpath")
  archeplaydatapath = os.getenv("archeplaydatapath")
  serviceid = request.json["serviceid"]
  code_type = request.json["type"]
  versionid = request.json["versionid"]
  versionname = request.json["versionname"]
  namespace = "default"
  resourceid = request.json["resourceid"]
  r=requests.get(metadatas3url)
  imagemetadata=r.json()
  jobregistryurl = imagemetadata['registryurl']+"/"
  resource_path="servicedesigns/"+serviceid+"/api/"+"v1/resources"+resourceid
  resource_configfile = resource_path+"/config.json"
  if code_type == "PYTHON_FLASK":
    resourceimagejobname = "docker-flask-gunicorn"
    resourcejobimageid = jobregistryurl+imagemetadata['images'][resourceimagejobname]['imagename']+":"+imagemetadata['images'][resourceimagejobname]['tag'] 
  containerstatus,container_message,container_response=create_resource_job(resource_path,resourcejobimageid,kubeconfigpath,resourceid,code_type,serviceid,versionid,versionname,namespace,archeplaydatapath)
  successmessage={
    "status": 200,
    "containerstatus": containerstatus,
    "container_response": container_response
  }
  return(successmessage)

@resource_api.route('/live/v1/resource/<resourceid>', methods=['GET'])
def getresource(resourceid):
    namespace = "default"
    fieldstring = 'metadata.name='+"resourcejob"+resourceid
    jobstatus,jobmessage = get_job_status(namespace,fieldstring)
    resource_job_status_data={
        "jobstatus": jobstatus,
        "jobmessage": jobmessage,
        "resourceid": resourceid
    }
    successmessage={
        "status": 200,
        "jobstatus_data": resource_job_status_data
    }
    return(successmessage)

@resource_api.route('/live/v1/resource/<serviceid>/<versionid>/<resourceid>/output', methods=['GET'])
def getoutput(serviceid,resourceid,versionid):
    resource_path="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid
    resource_outputfile=resource_path+"/output.json"
    namespace = "default"
    fieldstring = 'metadata.name='+"resourcejob"+resourceid
    status,status_message,resource_output_config=datafile.load_s3_file(resource_outputfile)
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
                "opstatus": status,
                "opstatmessage": status_message
            }
    else:
        resource_output=resource_output_config["state"]
        successmessage={
            "resource_output": resource_output,
            "status": 200
        }
    return(successmessage)

@resource_api.route('/live/v1/resource/<serviceid>/<versionid>/<resourceid>/logs', methods=['GET'])
def getlogs(serviceid,versionid,resourceid):
    resource_path="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid
    resource_logfile=resource_path+"/log.json"
    status,status_message,resource_logs_config=datafile.load_s3_file(resource_logfile)
    if status == "error":
        successmessage={
            "error_message":"failed to load resource logfile",
            "status": 400
        }
    else:
        successmessage={
            "resource_output": resource_logs_config,
            "status": 200
        }
    return(successmessage)

@resource_api.route('/live/v1/resource/<serviceid>/<versionid>/<resourceid>', methods=['DELETE'])
def deleteresource(serviceid,resourceid,versionid):
    namespace="default"
    labelstring = 'resourcejob='+'resourcejob'+resourceid
    resource_path="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid
    resource_outputfile=resource_path+"/output.json"
    deployment_status,deployment_status_message=delete_deployment(resourceid,namespace)
    service_status,service_status_message=delete_service(resourceid,namespace)
    job_status,job_status_message=delete_job(resourceid,namespace)
    pod_status,pod_status_message=delete_pod(namespace,labelstring)
    ingress_status,ingress_status_message=delete_ingress(resourceid,namespace)
    if deployment_status == "success":
        if service_status == "success":
            if job_status == "success":
                if pod_status == "success":
                    if ingress_status == "success":
                        delete_op_status,delete_op_status_message,delete_op_response=datafile.delete_s3_file(resource_outputfile)
                        if delete_op_status == "success":
                            status_message={
                                "status": 200,
                                "status_message": "resource_deleted_successfully"
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
                            "status_message": "ingress_deletion_failed",
                            "error_message": ingress_status_message
                        }
                else:
                    status_message={
                        "status": 400,
                        "status_message": "resource_pod_deletion_failed",
                        "error_message": pod_status_message
                    }
            else:
                status_message={
                    "status": 400,
                    "status_message": "resource_job_deletion_failed",
                    "error_message": job_status_message
                }
        else:
            status_message={
                    "status": 400,
                    "status_message": "resource_service_deletion_failed",
                    "error_message": service_status_message
                }
    else:
        status_message={
            "status": 400,
            "status_message": "resource_deployment_deletion_failed",
            "error_message": deployment_status
        }
    return(status_message)

@resource_api.route('/live/v1/resource/update', methods=['POST'])
def updateresource():
    serviceid = request.json["serviceid"]
    code_type = request.json["type"]
    versionid = request.json["versionid"]
    versionname = request.json["versionname"]
    resourceid = request.json["resourceid"]
    delete_before_update = deleteresource(serviceid,resourceid,versionid)
    time.sleep(20)
    print(delete_before_update)
    if delete_before_update['status'] == 200:
        print(delete_before_update['status'])
        print("Creating the update resource")
        update_resource = createresource()
        if update_resource['status'] == 200:
            successmessage={
                "status": 200,
                "containerstatus": update_resource['containerstatus'],
                "container_response": update_resource['container_response']
            }
            print("successmessagesuccess: ", successmessage)
            return(successmessage)
        else:
            errormessage={
                "status": 400,
                "containerstatus": update_resource['containerstatus'],
                "container_response": update_resource['container_response']
            }
            print("errormessage: ", errormessage)
            return(errormessage)
    success_message={
        "status": 200,
        "Status_message": "Resource_Updated_Successfully"
    }
    return(success_message)

@resource_api.route('/live/v1/resource/<serviceid>/<versionid>/<resourceid>/buildlog', methods=['GET'])
def getbuildlogs(serviceid,resourceid,versionid):
    resource_path="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid 
    resource_build_logfile=resource_path+"/buildlog.json"
    status,status_message,resource_logs_config=datafile.load_s3_file(resource_build_logfile)
    if status == "error":
        successmessage={
            "error_message":"failed to load build logfile",
            "status": 400
        }
    else:
        successmessage={
            "resource_output": resource_logs_config,
            "status": 200
        }
    return(successmessage)

@resource_api.route('/live/v1/resource/<serviceid>/<versionid>/<resourceid>/pushlog', methods=['GET'])
def getpushlogs(serviceid,resourceid,versionid):
    resource_path="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid 
    resource_push_logfile=resource_path+"/pushlog.json"
    status,status_message,resource_logs_config=datafile.load_s3_file(resource_push_logfile)
    if status == "error":
        successmessage={
            "error_message":"failed to load push logfile",
            "status": 400
        }
    else:
        successmessage={
            "resource_output": resource_logs_config,
            "status": 200
        }
    return(successmessage)

@resource_api.route('/live/v1/resource/<serviceid>/<versionid>/<resourceid>/consolelog', methods=['GET'])
def getconsolelogs(serviceid,resourceid,versionid):
    resource_path="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid 
    resource_console_logfile=resource_path+"/consolelog.json"
    namespace = "default"
    fieldstring = 'metadata.name='+"resourcejob"+resourceid
    status,status_message,resource_logs_config=datafile.load_s3_file(resource_console_logfile)
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
        resource_output=resource_output_config["state"]
        console_log_status,console_log_message,consolelog=get_console_log(namespace,fieldstring)
        if console_log_status == "success":
            successmessage={
                "resource_output": resource_output,
                "status": 200,
                "consolelog": consolelog
            }
        else:
            successmessage={
                "resource_output": resource_output,
                "status": 200,
                "consolelog": console_log_message
            }
    return(successmessage)