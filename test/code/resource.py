from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json

resource_api = Blueprint('resource_api', __name__)
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

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>', methods=['GET'])
def getapibyid(productid,serviceid,apiid):
	state_store=os.getenv("state_store")
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	status,statusmessage,api=load_s3_file(state_store,apipath)
	if status == "success":
		message = {"statusCode": 200,"body":api}
	else:
		message = {"errorMessgae": statusmessage, "Error": api}
	return(message)

@resource_api.route("/design/v1/api/<productid>/<serviceid>/<apiid>/version", methods=["POST"])
def createversion(productid,serviceid,apiid):
	iop = {
		"versionname": ""
	}
	state_store=os.getenv("state_store")
	versionname = request.json["versionname"]
	json_dict = request.get_json()
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	status,statusmessage,api=load_s3_file(state_store,apipath)
	if status == "success":
		version={
			'versionname': versionname,
					'versionid':uniqid('v-'),

					'resources': [
						]
		}
		if 'description' in json_dict:
			version['description']=request.json['description']
		api['versions'].append(version)
		writestatus,writestatusmessage,response=write_s3_file(state_store,apipath,api)
		if writestatus == "success":
			message={"statusCode":200, "body": api}
		else:
			message={"errorMessage": writestatusmessage, "Error": response}
	else:
		message={"errorMessage": statusmessage, "Error": api}
	return(message)

@resource_api.route("/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>", methods=["DELETE"])
def deleteversion(productid,serviceid,apiid,versionid):
	state_store=os.getenv("state_store")
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	status,statusmessage,api=load_s3_file(state_store,apipath)
	if status == "success":
		versionids = []
		for version in api["versions"]:
			versionids.append(version["versionid"])
		if versionid in versionids:
			for version in api["versions"]:
				if version["versionid"]==versionid:
					api["versions"].remove(version)
					status,statusmessage,response=write_s3_file(state_store,apipath,api)
			message={"statusCode": 200, "message": "Version Deleted"}
		else:
			message={"statusCode": 400,"errorMessage":"versionid does not exist"}
	else:
		message={"errorMessage": statusmessage, "Error": api}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/resource', methods=['POST'])
def createresource(productid,serviceid,apiid,versionid):
	iop={
		"resourcename":""
	}
	state_store=os.getenv("state_store")
	resourcename = request.json["resourcename"]
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	status,statusmessage,api=load_s3_file(state_store,apipath)
	if status == "success":
		for ver in api['versions']:
			if ver['versionid']==versionid:
				version=ver
		a= True
		while a is True:
			resourceid=uniqid('res')
			if resourceid in ver["resources"]:
				a= True
			else :
				a= False
		resource={
			"resourceid": resourceid,
			"resourcename": resourcename,
			"methods": [],
			"data": [{
					"db": [
						{
							"Ref": uniqid("db"),
							"tables": []
						}
						]
					}
				]
			}
		version['resources'].append(resourceid)
		status,statusmessage,response=write_s3_file(state_store,apipath,api)
		resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
		status,statusmessage,resources=write_s3_file(state_store,resourcepath,resource)
		message={"statusCode": 200, 'message':"Resource Created", 'body':resource}
	else:
		message={"statusCode": 400, 'message':statusmessage, 'errorMessage':api}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/resource', methods=['GET'])
def getresource(productid,serviceid,apiid,versionid):
	state_store=os.getenv("state_store")
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	status,statusmessage,api=load_s3_file(state_store,apipath)
	if status == "success":
		resources=[]
		for ver in api['versions']:
			for resourceid in ver["resources"]:
				resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
				status,statusmessage,resource=load_s3_file(state_store,resourcepath)
				if status == "success":
					resources.append(resource)
		message={"statusCode":200,"body":resources}
	else:
		message={"statusCode": 400,'errorMessage':api}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>', methods=['GET'])
def getresourcebyid(productid,serviceid,apiid,versionid,resourceid):
	state_store=os.getenv("state_store")
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	status,statusmessage,api=load_s3_file(state_store,apipath)
	if status == "success":
		for ver in api['versions']:
			if resourceid in ver["resources"]:
				resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
				status,statusmessage,resource=load_s3_file(state_store,resourcepath)
				if status == "success":
					message={"statusCode":200,"body":resource}
				else:
					message={"statusCode":400,"errorMessage":resource}
			else:
				message={"statusCode":400,"errorMessage":"resourceid does not exist"}
	else:
		message={"statusCode": 400,'errorMessage':api}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>', methods=['DELETE'])
def deleteresource(productid,serviceid,apiid,versionid,resourceid):
	state_store=os.getenv("state_store")
	apipath= "services/"+productid+"/"+serviceid+"/api/"+apiid+".json"
	status,statusmessage,api=load_s3_file(state_store,apipath)
	if status == "success":
		for ver in api['versions']:
			if resourceid in ver["resources"]:
				resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
				delstatus,statusmessage,response=delete_s3_file(state_store,resourcepath)
				ver["resources"].remove(resourceid)
				status,statusmessage,response=write_s3_file(state_store,apipath,api)
				if delstatus == "success" and status == "success":
					message={"statusCode":200,"message":"resource deleted"}
				else:
					message={"statusCode":400,"errorMessage":"resource deletion failed"}
			else:
				message={"statusCode":400,"errorMessage":"resourceid does not exist"}
	else:
		message={"statusCode": 400,'errorMessage':api}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/method', methods=['POST'])
def createmethod(productid,serviceid,apiid,versionid,resourceid):
	iop = {
		"methodtype": "",
        "path": ""
	}
	state_store=os.getenv("state_store")
	methodtype=request.json["methodtype"]
	path=request.json["path"]
	json_dict = request.get_json()
	resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
	status,statusmessage,resource=load_s3_file(state_store,resourcepath)
	if status == "success":
		if resource["methods"] == []:
			methodid = uniqid('meth')
			method={"Ref": methodid}
			resource["methods"].append(method)
		elif resource["methods"] != []:
			methodids=[]
			for method in resource["methods"]:
				methodids.append(method["Ref"])
			a= True
			while a is True:
				methodid=uniqid('meth')
				if methodid in methodids:
					a= True
				else :
					a= False
			method={"Ref": methodid}
			resource["methods"].append(method)
		resstatus,resstatusmessage,res=write_s3_file(state_store,resourcepath,resource)
		methodjson={
			"methodtype": methodtype,
			"methodpath": path,
			"methodid": methodid,
			"codetype": "python",
			"python": {
				"codepath": "code/"+methodid+".py",
				"requirement": "code/requirement.txt"
			}
		}
		if "description" in json_dict:
			methodjson["description"] = request.json["description"]
		methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
		methstatus,methstatusmessage,methres=write_s3_file(state_store,methodpath,methodjson)
		if methstatus == "success":
			message={"statusCode":200, "body": methodjson}
		else:
			message={"errorMessage": methstatus,"Error": methres}
	else:
		message={"errorMessage": statusmessage,"Error":resource}
	return(messages)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/<methodid>', methods=['DELETE'])
def deletemethod(productid,serviceid,apiid,versionid,resourceid,methodid):
	state_store=os.getenv("state_store")
	resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
	status,statusmessage,resource=load_s3_file(state_store,resourcepath)
	if status == "success":
		methodids=[]
		for method in resource["methods"]:
			methodids.append(method["Ref"])
		if methodid in methodids:
			for method in resource["methods"]:
				if method["Ref"]==methodid:
					resource["methods"].remove(method)
			methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
			delstatus,delstatusmessage,delres=delete_s3_file(state_store,methodpath)
			if delstatus == "success":
				message={"statusCode":200,"message":"method deleted"}
			else:
				message={"statusCode":400,"message":"method deletion failed"}
		else:
			message={"statusCode":400,"message":"methodid does not exist"}
	else:
		message={"errorMessage":statusmessage,"Error":resource}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/<methodid>', methods=['PATCH'])
def updatemethod(productid,serviceid,apiid,versionid,resourceid,methodid):
	state_store=os.getenv("state_store")
	json_dict=request.get_json()
	methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
	status,statusmessage,method=load_s3_file(state_store,methodpath)
	if status == "success":
		if "inputschema" in json_dict:
			method['inputschema']=request.json['inputschema']
		if "outputschema" in json_dict:
			method['outputschema']=request.json['outputschema']
		if "requirements" in json_dict:
			method['requirements']=request.json['requirements']
		writestatus,statusmessage,response=write_s3_file(state_store,methodpath,method)
		if writestatus == "success":
			message={"statusCode": 200, 'body':method}
		else:
			message={"statusCode": 400, "errorMessage":response}
	else:
		message={"errorMessage":statusmessage,"Error":method}
	return(message)