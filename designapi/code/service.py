from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json
import datafile
import shutil,glob

logger=logging.getLogger()
service_api = Blueprint('service_api', __name__)

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

@service_api.route('/design/v1/service/<productid>', methods=['POST'])
def createservice(productid):
	iop = {
        "servicename": "",
		"description": "",
		"servicetype": "",
		"optionname": ""
	}
	userid = request.headers["userid"]
	servicename = request.json["servicename"]
	servicetype = request.json["servicetype"]
	optionname = request.json["optionname"]
	json_dict = request.get_json()
	servicepath= "services/"+productid+"/services.json"
	status,statusmessage,services=datafile.load_s3_file(servicepath)
	if status != "success":
		services=[]
	serviceids = []
	for svc in services:
		serviceids.append(svc["serviceid"])
	a = True
	while a is True:
		serviceid=uniqid('service')
		if serviceid in serviceids:
			a = True
		else:
			a = False
	service={
		'productid':productid,
		'serviceid':serviceid,
		'userid':userid,
		'servicename':servicename,
		'servicetype':servicetype,
		'optionname':optionname,
		'tagnames':[]
	}
	if "description" in json_dict:
		service["description"]=request.json["description"]
	apiid=uniqid('api')
	api={
		'productid':productid,
		'serviceid':serviceid,
		'apiid':apiid,
		'userid':userid,
		'apiname':request.json['servicename'],
		'versions': [{
				'versionname': 'v1',
				'versionid':uniqid('v-'),
				'description': 'default version',
				'resources': [
					]
			}],
		'deploy': {
			'cloud': 'aws',
			'deployplatform': 'eks',
			'image': 'docker',
			'imagerepo': 'ecr'
		}
		}
	if 'description' in json_dict:
		api['description']=request.json['description']
	service['apiid']=api['apiid']
	services.append(service)
	status,statusmessage,response = datafile.write_s3_file(servicepath,services)
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	statusapi,statusmessageapi,resapi = datafile.write_s3_file(apipath,api)
	if status == "success":
		message = {"statusCode": 200, 'message':'New Service Created','body': service}
	else:
		message = {"statusCode": 400, 'message': statusmessage, 'Error': response}
	return(message)

@service_api.route("/design/v1/service/templates", methods=["GET"])
def listtemplates():
	try:
		templatepath="/home/app/web/archeplay/template"
		templatefiles=glob.glob(templatepath+"/servicetemplates/*", recursive = True)
		templates=[]
		for template in templatefiles:
			with open(template,"r") as f:
				tempdata=f.read()
				templatedata=json.loads(tempdata)
				del templatedata["deploysteps"]
				templates.append(templatedata)
		message={"statusCode":200,"body":templates}
		return(message)
	except Exception as e:
		message={"statusCode":400,"errorMessage":str(e)}
		return(message)

@service_api.route("/design/v1/service/<productid>", methods=["GET"])
def getservice(productid):
	servicepath = "services/"+productid+"/services.json"
	status,statusmessage,services = datafile.load_s3_file(servicepath)
	if status != "success":
		services=[]
	message = {"statusCode": 200, "body": services}
	return(message)

@service_api.route("/design/v1/service/<productid>/<serviceid>", methods=["GET"])
def getservicebyid(productid,serviceid):
	servicepath= "services/"+productid+"/services.json"
	status,statusmessage,services=datafile.load_s3_file(servicepath)
	if status == "success":
		serviceids = []
		for svc in services:
			serviceids.append(svc["serviceid"])
		if serviceid in serviceids:
			service={}
			for svc in services:
				if svc["serviceid"]==serviceid:
					service=svc
				if "status" not in svc:
					service["status"]="design"
			message={"statusCode": 200,"body":service}
		else:
			message={"statusCode": 400,"errorMessage":"serviceid does not exist"}
	else:
		message={"statusCode": 400, "errorMessage": services}
	return(message)


@service_api.route('/design/v1/service/<productid>/<serviceid>', methods=['DELETE'])
def deleteservice(productid,serviceid):
	servicepath= "services/"+productid+"/services.json"
	status,statusmessage,services=datafile.load_s3_file(servicepath)
	if status == "success":
		serviceids = []
		for svc in services:
			serviceids.append(svc["serviceid"])
		if serviceid in serviceids:
			for svc in services:
				if svc["serviceid"] == serviceid:
					services.remove(svc)
					svcprefix="servicedesigns/"+serviceid
					delstatus,delstatusmessage=datafile.delete_folders(svcprefix)
			status,statusmessage,response=datafile.write_s3_file(servicepath,services)
			message={"statusCode": 200, 'message':'Service Deleted'}
		else:
			message={"statusCode": 400,"errorMessage":"serviceid does not exist"}
	else:
		message={"errorMessage": statusmessage, "Error": services}
	return(message)

@service_api.route("/design/v1/service/<productid>/<serviceid>/updatestatus", methods=["POST"])
def updateservicebyid(productid,serviceid):
	servicepath= "services/"+productid+"/services.json"
	status,statusmessage,services=datafile.load_s3_file(servicepath)
	if status == "success":
		serviceids = []
		for svc in services:
			serviceids.append(svc["serviceid"])
		if serviceid in serviceids:
			service={}
			for svc in services:
				if svc["serviceid"]==serviceid:
					svc["status"]="design"
					service=svc
			status,statusmessage,writeservice=datafile.write_s3_file(servicepath,services)
			if status == "error":
				message={"statusCode":400,"errorMessage":statusmessage}
				return(message)
			message={"statusCode": 200,"body":service}
		else:
			message={"statusCode": 400,"errorMessage":"serviceid does not exist"}
	else:
		message={"statusCode": 400, "errorMessage": services}
	return(message)
	