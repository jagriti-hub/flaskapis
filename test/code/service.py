from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json

service_api = Blueprint('service_api', __name__)
s3_client=boto3.client("s3")

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

def list_object_byprefix(bucket_name, prefix):
    try:
        list_object = s3_client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix
        )
        object_contents = list_object["Contents"]
        object_keys = []
        for objects in object_contents:
            object_keys.append(objects["Key"])
        return("success",object_keys)
    except Exception as e:
        return("error",str(e))

def load_s3_file(bucket_name, filepath):
	try:
		file_object=s3_client.get_object(Bucket=bucket_name,Key=filepath)["Body"].read()
		data=json.loads(file_object)
		successmessage=filepath+" loaded Successfully"
		return("success", successmessage, data)
	except Exception as Error:
		errormessage=filepath+" not found"
		return("error", errormessage, str(Error))
		
def write_s3_file(bucket_name, path, data):
	try:
		datastring=json.dumps(data)
		s3_response=s3_client.put_object(Bucket=bucket_name,Key=path,Body=datastring)
		status="success"
		successmessage=path+" written Successfully"
		return(status, successmessage, s3_response)
	except Exception as Error:
		status="error"
		errormessage=path+" written Failed"
		return(status, errormessage, str(Error))

def delete_s3_file(bucket_name,path):
	try:
		s3_response=response = s3_client.delete_object(Bucket=bucket_name,Key=path)
		status="success"
		successmessage=path+" deleted Successfully"
		return(status, successmessage, s3_response)
	except Exception as Error:
		status="error"
		errormessage=path+" deletion Failed"
		return(status, errormessage, str(Error))

@service_api.route('/design/v1/service/<productid>', methods=['POST'])
def createservice(productid):
	iop = {
        "servicename": "",
		"description": ""
	}
	state_store=os.getenv("state_store")
	userid = request.headers["userid"]
	servicename = request.json["servicename"]
	json_dict = request.get_json()
	servicepath= "services/"+productid+"/services.json"
	status,statusmessage,services=load_s3_file(state_store,servicepath)
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
		'servicename':servicename
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
			}]
		}
	if 'description' in json_dict:
		api['description']=request.json['description']
	service['apiid']=api['apiid']
	services.append(service)
	status,statusmessage,response = write_s3_file(state_store,servicepath,services)
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	statusapi,statusmessageapi,resapi = write_s3_file(state_store,apipath,api)
	if status == "success":
		message = {"statusCode": 200, 'message':'New Service Created','body': service}
	else:
		message = {"statusCode": 400, 'message': statusmessage, 'Error': response}
	return(message)

@service_api.route("/design/v1/service/<productid>", methods=["GET"])
def getservice(productid):
	state_store=os.getenv("state_store")
	servicepath = "services/"+productid+"/services.json"
	status,statusmessage,services = load_s3_file(state_store,servicepath)
	if status == "success":
		message = {"statusCode": 200, "body": services}
	else:
		message = {"statusCode": 400, "errorMessage": statusmessage}
	return(message)

@service_api.route("/design/v1/service/<productid>/<serviceid>", methods=["GET"])
def getservicebyid(productid,serviceid):
	state_store=os.getenv("state_store")
	servicepath= "services/"+productid+"/services.json"
	status,statusmessage,services=load_s3_file(state_store,servicepath)
	if status == "success":
		serviceids = []
		for svc in services:
			serviceids.append(svc["serviceid"])
		if serviceid in serviceids:
			service={}
			for svc in services:
				if svc["serviceid"]==serviceid:
					service=svc
			message={"statusCode": 200,"body":service}
		else:
			message={"statusCode": 400,"errorMessage":"serviceid does not exist"}
	else:
		message={"errorMessage": statusmessage, "Error": services}
	return(message)


@service_api.route('/design/v1/service/<productid>/<serviceid>', methods=['DELETE'])
def deleteservice(productid,serviceid):
	state_store=os.getenv("state_store")
	servicepath= "services/"+productid+"/services.json"
	status,statusmessage,services=load_s3_file(state_store,servicepath)
	if status == "success":
		serviceids = []
		for svc in services:
			serviceids.append(svc["serviceid"])
		if serviceid in serviceids:
			for svc in services:
				if svc["serviceid"] == serviceid:
					services.remove(svc)
			status,statusmessage,response=write_s3_file(state_store,servicepath,services)
			message={"statusCode": 200, 'message':'Service Deleted'}
		else:
			message={"statusCode": 400,"errorMessage":"serviceid does not exist"}
	else:
		message={"errorMessage": statusmessage, "Error": services}
	return(message)