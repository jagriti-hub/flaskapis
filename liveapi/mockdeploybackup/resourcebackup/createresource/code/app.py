from flask import Flask, jsonify
from flask import request
import sys,os,boto3
import logging,json,requests
import kubernetes
from kubernetes import client, config

def create_resource_job(resource_path,resourcejobimageid,kubeconfigpath,resourceid,state_store,namespace,type):
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
        name="resourcejob"+resourceid,
        image=resourcejobimageid,
        volume_mounts=[mount2],
        command=["python","-u","app.py",resource_path,resourceid,type],
        env=[{"name": "state_store","value":state_store}],
        image_pull_policy="Always"
    )
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"resourcejob": "resourcejob"+resourceid}),
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
        metadata=client.V1ObjectMeta(name="resourcejob"+resourceid),
        spec=spec)
    api_response = batch_v1.create_namespaced_job(
        body=job,
        namespace=namespace)
    success_message = resourceid+" Deploy Job Intitated"
    return("success",success_message,api_response.status)
  except Exception as Error:
    error_message=resourceid+" Failed to Intitate Deploy Job"
    return("error",error_message,str(Error))

app = Flask(__name__)
@app.route('/v1/live/resource', methods=['POST'])
def createresource():
  metadatas3url = os.getenv("imagemetaurl")
  kubeconfigpath = os.getenv("kubeconfigpath")
  state_store = os.getenv("state_store")
  tenantid = request.json["tenantid"]
  serviceid = request.json["serviceid"]
  type = request.json["type"]
  namespace = "default"
  resourceid = request.json["resourceid"]
  r=requests.get(metadatas3url)
  imagemetadata=r.json()
  jobregistryurl = imagemetadata['registryurl']+"/"
  print(imagemetadata)
  resource_path=tenantid+"/"+serviceid+"/api/"+resourceid
  resource_configfile = resource_path+"/config.json"
  if type == "PYTHON_FLASK":
    resourceimagejobname = "docker-flask-gunicorn"
    resourcejobimageid = jobregistryurl+imagemetadata['images'][resourceimagejobname]['imagename']+":"+imagemetadata['images'][resourceimagejobname]['tag'] 
  containerstatus,container_message,container_response=create_resource_job(resource_path,resourcejobimageid,kubeconfigpath,resourceid,state_store,namespace,type)
  successmessage={
    "status": "200",
    "containerstatus": containerstatus,
    "container_response": container_response
  }
  return(successmessage)