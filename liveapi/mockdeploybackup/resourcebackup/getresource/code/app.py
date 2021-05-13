from flask import Flask, jsonify
from flask import request
import sys,os,boto3
import logging,json
import kubernetes
from kubernetes import client, config

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


app = Flask(__name__)
@app.route('/v1/live/resource/<resourceid>', methods=['GET'])
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

