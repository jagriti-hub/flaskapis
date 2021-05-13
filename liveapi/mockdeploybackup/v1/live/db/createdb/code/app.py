from flask import Flask, jsonify
from flask import request
import sys,os,boto3
import logging,json,requests
import kubernetes
from kubernetes import client, config

def create_database_job(db_configfile,dbjobimageid,kubeconfigpath,dbid,state_store,namespace):
  try:
    print(kubeconfigpath)
    config.load_kube_config(kubeconfigpath)

    volume2=client.V1Volume(
      name="kubeconfig",
      host_path={"path": kubeconfigpath}
    )
    mount2 = client.V1VolumeMount(
      name="kubeconfig",
      mount_path="/home/app/web/kubeconfig"
    )
    batch_v1 = client.BatchV1Api()
    container = client.V1Container(
        name="dbjob"+dbid,
        image=dbjobimageid,
        volume_mounts=[mount2],
        command=["python","-u","app.py",db_configfile,dbid],
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
    return("success",success_message,api_response.status)
  except Exception as Error:
    error_message=dbid+" Failed to Intitate Deploy Job"
    return("error",error_message,str(Error))

app = Flask(__name__)
@app.route('/v1/live/db', methods=['POST'])
def createdb():
  metadatas3url = os.getenv("imagemetaurl")
  kubeconfigpath = os.getenv("kubeconfigpath")
  state_store = os.getenv("state_store")
  tenantid = request.json["tenantid"]
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
  containerstatus,container_message,container_response=create_database_job(db_configfile,dbjobimageid,kubeconfigpath,dbid,state_store,namespace)
  successmessage={
    "status": "200",
    "containerstatus": containerstatus,
    "container_response": container_response
  }
  return(successmessage)