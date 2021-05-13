from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json
import datafile

logger=logging.getLogger()
testcase_api = Blueprint('testcase_api', __name__)

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

def getmethod(productid,serviceid,apiid,versionid,resourceid):
	resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
	status,statusmessage,resource=datafile.load_s3_file(resourcepath)
	if status == "success":
		methods=[]
		if resource["methods"] != []:
			for method in resource["methods"]:
				methodid=method["Ref"]
				methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
				methstatus,methstatusmessage,loadmethod=datafile.load_s3_file(methodpath)
				if methstatus == "success":
					methods.append(loadmethod)
			message={"statusCode":200,"body":methods}
		else:
			message={"statusCode":200,"body":methods}
	else:
		message={"statusCode":400,"errorMessage":resource}
	return(message)

# @testcase_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/createtestcase', methods=['POST'])	
# def createtestcase(productid,serviceid,apiid,versionid,resourceid):
# 	methodmessage=getmethod(productid,serviceid,apiid,versionid,resourceid)
# 	testcaseid = uniqid("tc_")
# 	methoddata = []
# 	for method in methodmessage["body"]:
# 		methodpath=method["methodpath"]
# 		methodtype=method["methodtype"]
# 		methodid=method["methodid"]
# 		methoddata.append({"methodpath": methodpath,"methodtype": methodtype,"methodid": methodid})
# 	testcase_data={
# 		"testcasename": "",
# 		"testcaseid": testcaseid,
# 		"method": methoddata
# 	}
# 	message={"statusCode": 200, "body": testcase_data}
# 	return(message)

@testcase_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/addtestcase', methods=['POST'])	
def addtestcases(productid,serviceid,apiid,versionid,resourceid):
	testcasename = request.json["testcasename"]
	testcaseid = uniqid("tc_")
	methodid = request.json["methodid"]
	methodpath = request.json["methodpath"]
	methodtype = request.json["methodtype"]
	testcasedata = {
		"body": "",
		"pathparameters": {},
		"queryparameters": "",
		"headers": "",
		"testcasename": testcasename,
		"testcaseid": testcaseid,
		"methodid": methodid,
		"methodpath": methodpath,
		"methodtype": methodtype
	}
	testcasepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/testcases/"+methodid+"/" + testcaseid + ".json"
	testcasestatus,testcasestatusmessage,testres=datafile.write_s3_file(testcasepath,testcasedata)
	if testcasestatus == "success":
		message={"statusCode": 200, "body": testcasedata}
	else:
		message={"statusCode": 400, "errorMessage": testres}
	return(message)
	
@testcase_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/<methodid>/<testcaseid>', methods=['DELETE'])	
def deletetestcases(productid,serviceid,apiid,versionid,resourceid,methodid,testcaseid):
	testcasepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/testcases/"+methodid+"/" + testcaseid + ".json"
	deletestatus,deletestatusmessage,deleteresponse=datafile.delete_s3_file(testcasepath)
	if deletestatus == "success":
		message={"statusCode": 200, "body": "testcase successfully deleted"}
	else:
		message={"statusCode": 400, "errorMessage": deleteresponse}
	return(message)
	
@testcase_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/<methodid>/<testcaseid>', methods=['PATCH'])	
def updatetestcases(productid,serviceid,apiid,versionid,resourceid,methodid,testcaseid):
	json_dict=request.get_json()
	testcasepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/testcases/"+methodid+"/" + testcaseid + ".json"
	status,statusmessage,testcase=datafile.load_s3_file(testcasepath)
	if status == "success":
		if "body" in json_dict:
			testcase["body"] = request.json["body"]
		if "headers" in json_dict:
			testcase["headers"] = request.json["headers"]
		if "pathparameters" in json_dict:
			testcase["pathparameters"] = request.json["pathparameters"]
		if "queryparameters" in json_dict:
			testcase["queryparameters"] = request.json["queryparameters"]
		if "testcasename" in json_dict:
			testcase["testcasename"] = request.json["testcasename"]
	testcasepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/testcases/"+methodid+"/" + testcaseid + ".json"
	testcasestatus,testcasestatusmessage,testres=datafile.write_s3_file(testcasepath,testcase)
	if testcasestatus == "success":
		message={"statusCode": 200, "body": testcase}
	else:
		message={"statusCode": 400, "errorMessage": testres}
	return(message)
	
@testcase_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/getalltestcases', methods=['GET'])	
def getalltestcases(productid,serviceid,apiid,versionid,resourceid):
    testcasemethodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/testcases"
    methodstatus,methodstatusmessage,methodid = datafile.list_directory(testcasemethodpath)
    if methodstatus == "success":
    	testcases =[]
    	try:
    		for item in methodid:
    			testcasepath = "servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/testcases/" + item
    			testcasestatus,testcasestatusmessage,files = datafile.list_directory(testcasepath)
    			try:
    				for filename in files:
    					testcasefile = testcasepath + "/" + filename
    					status,statusmessage,testcase=datafile.load_s3_file(testcasefile)
    					testcases.append(testcase)
    			except Exception as e:
    				print(str(e))
    	except Exception as e:
    		print(str(e))
    	message = {"statusCode": 200, "body": testcases}
    else:
    	testcases = []
    	message = {"statusCode": 200, "body": testcases}
    return(message)
