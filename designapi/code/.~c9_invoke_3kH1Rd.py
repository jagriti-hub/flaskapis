from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json
import datafile

resource_api = Blueprint('resource_api', __name__)

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
 
def consolidate_code(template):
	action = {}
	data_code = ""
	requirements = []
	function_code = ""
	function_call = ""
	import_code = ""
	import_full_code = []
	for snippet in template["snippets"]["snippetorder"]:
	    snippetid = snippet["snippetid"]
	    cd_tem=["import_code","function_code","function_call","data_code"]
	    for cd in cd_tem:
	    	if cd in template["snippets"][snippetid]:
	    		action[cd] = template["snippets"][snippetid][cd]
	    if action["data_code"] not in data_code:
	        data_code = data_code + action["data_code"]
	    for module in template["snippets"][snippetid]["requirements"]:
	        if module not in requirements:
	            requirements.append(module)
	    function_code = function_code + action["function_code"]
	    function_call = function_code + action["function_call"]
	    import_data = action["import_code"].split("\n")
	    for import_item in import_data:
	        if import_item not in import_full_code:
	            import_full_code.append(import_item)
	for import_item in import_full_code:
	    import_code = import_code+import_item+"\n"
	full_code = import_code + data_code + function_code + function_call
	return(full_code,requirements)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>', methods=['GET'])
def getapibyid(productid,serviceid,apiid):
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	status,statusmessage,api=datafile.load_s3_file(apipath)
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
	versionname = request.json["versionname"]
	json_dict = request.get_json()
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	status,statusmessage,api=datafile.load_s3_file(apipath)
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
		writestatus,writestatusmessage,response=datafile.write_s3_file(apipath,api)
		if writestatus == "success":
			message={"statusCode":200, "body": api}
		else:
			message={"errorMessage": writestatusmessage, "Error": response}
	else:
		message={"errorMessage": statusmessage, "Error": api}
	return(message)

@resource_api.route("/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>", methods=["DELETE"])
def deleteversion(productid,serviceid,apiid,versionid):
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	status,statusmessage,api=datafile.load_s3_file(apipath)
	if status == "success":
		versionids = []
		for version in api["versions"]:
			versionids.append(version["versionid"])
		if versionid in versionids:
			for version in api["versions"]:
				if version["versionid"]==versionid:
					api["versions"].remove(version)
					status,statusmessage,response=datafile.write_s3_file(apipath,api)
					versionprefix="servicedesigns/"+serviceid+"/api/"+versionid
					delstatus,delstatusmessage=datafile.delete_folders(versionprefix)
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
	resourcename = request.json["resourcename"]
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	status,statusmessage,api=datafile.load_s3_file(apipath)
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
							"db": []
							}
						]
					}
				version['resources'].append(resourceid)
				status,statusmessage,response=datafile.write_s3_file(apipath,api)
				resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
				status,statusmessage,resources=datafile.write_s3_file(resourcepath,resource)
				message={"statusCode": 200, 'message':"Resource Created", 'body':resource}
			else:
				message={"statusCode": 400, 'message': "versionid does not exist"}
	else:
		message={"statusCode": 400, 'message':statusmessage, 'errorMessage':api}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/resource', methods=['GET'])
def getresource(productid,serviceid,apiid,versionid):
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	status,statusmessage,api=datafile.load_s3_file(apipath)
	if status == "success":
		resources=[]
		for ver in api['versions']:
			for resourceid in ver["resources"]:
				resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
				status,statusmessage,resource=datafile.load_s3_file(resourcepath)
				if status == "success":
					resources.append(resource)
		message={"statusCode":200,"body":resources}
	else:
		message={"statusCode": 400,'errorMessage':api}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>', methods=['GET'])
def getresourcebyid(productid,serviceid,apiid,versionid,resourceid):
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	status,statusmessage,api=datafile.load_s3_file(apipath)
	if status == "success":
		for ver in api['versions']:
			if ver["versionid"]==versionid:
				if resourceid in ver["resources"]:
					resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
					status,statusmessage,resource=datafile.load_s3_file(resourcepath)
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
	apipath= "servicedesigns/"+serviceid+"/api/config.json"
	status,statusmessage,api=datafile.load_s3_file(apipath)
	if status == "success":
		for ver in api['versions']:
			if ver["versionid"]==versionid:
				if resourceid in ver["resources"]:
					resourceprefix="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid
					delstatus,statusmessage=datafile.delete_folders(resourceprefix)
					ver["resources"].remove(resourceid)
					status,statusmessage,response=datafile.write_s3_file(apipath,api)
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
	methodtype=request.json["methodtype"]
	json_dict = request.get_json()
	resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
	status,statusmessage,resource=datafile.load_s3_file(resourcepath)
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
		resstatus,resstatusmessage,res=datafile.write_s3_file(resourcepath,resource)
		methodjson={
			"methodtype": methodtype,
			"methodid": methodid,
			"codetype": "python",
			"language": "python3.6",
			"servicetype":"dynamodb_eks_flask",
			"requirements": "",
			"import_code":"",
			"function_code":"",
			"main_code":"",
			"type_code":""
		}
		if "path" in  json_dict:
			methodjson["methodpath"]=request.json["path"]
		if "description" in json_dict:
			methodjson["description"] = request.json["description"]
		methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
		codestring=methodjson["import_code"]+"\n"+methodjson["function_code"]+"\n"+methodjson["main_code"]+"\n"+methodjson["type_code"]
		codepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/"+methodid+".py"
		codestatus,codestatusmessage,code=datafile.write_txt_file(codepath,codestring)
		requirement=methodjson["requirements"]
		requirementpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/requirement.txt"
		requirementstatus,requirementstatusmessage,req=datafile.write_txt_file(requirementpath,requirement)
		methstatus,methstatusmessage,methres=datafile.write_s3_file(methodpath,methodjson)
		if methstatus == "success" and codestatus == "success" and requirementstatus == "success":
			message={"statusCode":200, "body": methodjson}
		else:
			message={"errorMessage": methstatus,"Error": methres}
	else:
		message={"errorMessage": statusmessage,"Error":resource}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/<methodid>', methods=['DELETE'])
def deletemethod(productid,serviceid,apiid,versionid,resourceid,methodid):
	resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
	status,statusmessage,resource=datafile.load_s3_file(resourcepath)
	if status == "success":
		methodids=[]
		for method in resource["methods"]:
			methodids.append(method["Ref"])
		if methodid in methodids:
			for method in resource["methods"]:
				if method["Ref"]==methodid:
					resource["methods"].remove(method)
					resstatus,resstatusmessage,res=datafile.write_s3_file(resourcepath,resource)
			methodprefix="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid
			methodpath=methodprefix+".json"
			status,statusmessage,delmeth=datafile.delete_s3_file(methodpath)
			delstatus,delstatusmessage=datafile.delete_folders(methodprefix)
			if status == "success" and delstatus == "success":
				message={"statusCode":200,"message":"method deleted"}
			else:
				message={"statusCode":400,"message":delstatusmessage}
		else:
			message={"statusCode":400,"message":"methodid does not exist"}
	else:
		message={"errorMessage":statusmessage,"Error":resource}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/<methodid>', methods=['PATCH'])
def updatemethod(productid,serviceid,apiid,versionid,resourceid,methodid):
	json_dict=request.get_json()
	methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
	status,statusmessage,method=datafile.load_s3_file(methodpath)
	if status == "success":
		if "inputschema" in json_dict:
			method['inputschema']=request.json['inputschema']
		if "outputschema" in json_dict:
			method['outputschema']=request.json['outputschema']
		if "requirements" in json_dict:
			method['requirements']=request.json['requirements']
			requirementpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/requirement.txt"
			reqwritestatus,reqwritestatusmessage,req=datafile.write_txt_file(requirementpath,method['requirements'])
		if "import_code" in json_dict:
			method["import_code"]=request.json["import_code"]
		if "function_code" in json_dict:
			method["function_code"]=request.json["function_code"]
		if "main_code" in json_dict:
			method["main_code"]=request.json["main_code"]
		if "type_code" in json_dict:
			method["type_code"]=request.json["type_code"]
		codestring=method["import_code"]+"\n"+method["function_code"]+"\n"+method["main_code"]+"\n"+method["type_code"]
		codepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/"+methodid+".py"
		codestatus,codestatusmessage,code=datafile.write_txt_file(codepath,codestring)
		writestatus,statusmessage,response=datafile.write_s3_file(methodpath,method)
		if writestatus == "success" and codestatus == "success":
			message={"statusCode": 200, 'body':method}
		else:
			message={"statusCode": 400, "errorMessage":response}
	else:
		message={"errorMessage":statusmessage,"Error":method}
	return(message)

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/method', methods=['GET'])
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

@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>/<methodid>', methods=['GET'])
def getmethodbyid(productid,serviceid,apiid,versionid,resourceid,methodid):
	methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
	status,statusmessage,method=datafile.load_s3_file(methodpath)
	if status == "success":
		message={"statusCode":200,"body":method}
	else:
		message={"erroeMessage":statusmessage,"Error":method}
	return(message)

# @resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>', methods=['POST'])
# def generatemethod(productid,serviceid,apiid,versionid,resourceid):
# 	resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
# 	status,statusmessage,resource=datafile.load_s3_file(resourcepath)
# 	actions = request.json["actions"]
# 	versionname = request.json["versionname"]
# 	methodmessage=getmethod(productid,serviceid,apiid,versionid,resourceid)
# 	if methodmessage["statusCode"] == 200:
# 		if methodmessage["body"] !=[]:
# 			for method in methodmessage["body"]:
# 				for action in actions:
# 					action["methodpath"]=action["methodpath"].replace("{","<")
# 					action["methodpath"]=action["methodpath"].replace("}",">")
# 					if action["methodpath"] == method["methodpath"] and action["methodtype"] == method["methodtype"]:
# 						actions.remove(action)
# 	else:
# 		return(methodmessage)
# 	autopoppulate={
# 			"resourceid":resourceid,
# 			"serviceid":serviceid,
# 			"versionid":versionid,
# 			"actions": actions
# 		}
# 	actionlist=[]
# 	for act in autopoppulate["actions"]:
# 		methodid = uniqid("meth")
# 		act["methodid"]=methodid
# 		act["methodpath"]=act["methodpath"].replace("{","<")
# 		act["methodpath"]=act["methodpath"].replace("}",">")
# 		if act["methodpath"]!="":
# 			apicallpath="/"+versionname+"/"+resource["resourcename"]+act["methodpath"]
# 		else:
# 			apicallpath="/"+versionname+"/"+resource["resourcename"]
# 		method={"Ref": methodid}
# 		resource["methods"].append(method)
# 		resstatus,resstatusmessage,res=datafile.write_s3_file(resourcepath,resource)
# 		if resstatus == "error":
# 			message={"statusCode":400,"errorMessage":res}
# 			return(message)
# 		methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
# 		act["import_code"]=act["import_code"].replace("METHODID",methodid)
# 		act["import_code"]=act["import_code"].replace("METHODPATH",apicallpath)
# 		act["function_code"]=act["function_code"].replace("METHODID",methodid)
# 		act["function_code"]=act["function_code"].replace("METHODPATH",apicallpath)
# 		act["main_code"]=act["main_code"].replace("METHODID",methodid)
# 		act["main_code"]=act["main_code"].replace("METHODPATH",apicallpath)
# 		act["type_code"]=act["type_code"].replace("METHODID",methodid)
# 		act["type_code"]=act["type_code"].replace("METHODPATH",apicallpath)
# 		codestring=act["import_code"]+"\n"+act["function_code"]+"\n"+act["main_code"]+"\n"+act["type_code"]
# 		codepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/"+methodid+".py"
# 		codestatus,codestatusmessage,code=datafile.write_txt_file(codepath,codestring)
# 		if codestatus=="error":
# 			message={"statusCode":400,"errorMessage":code}
# 			return(message)
# 		requirement=act["requirements"]
# 		reqstring=""
# 		for i in requirement:
# 			reqstring=reqstring+i+"\n"
# 		# act["requirements"]=reqstring
# 		requirementpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/requirement.txt"
# 		requirementstatus,requirementstatusmessage,req=datafile.write_txt_file(requirementpath,reqstring)
# 		if requirementstatus == "error":
# 			message={"statusCode":400,"errorMessage":req}
# 			return(message)
# 		methstatus,methstatusmessage,methres=datafile.write_s3_file(methodpath,act)
# 		if methstatus == "error":
# 			message={"statusCode":400,"errorMessage":code}
# 			return(message)
# 		if methstatus == "success" and codestatus == "success" and requirementstatus == "success":
# 			actionlist.append(act)
# 	message={"statusCode": 200,"body": actionlist}
# 	return(message)
	
@resource_api.route('/design/v1/api/<productid>/<serviceid>/<apiid>/<versionid>/<resourceid>', methods=['POST'])
def generatemethod(productid,serviceid,apiid,versionid,resourceid):
	resourcepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
	status,statusmessage,resource=datafile.load_s3_file(resourcepath)
	actions = request.json["actions"]
	versionname = request.json["versionname"]
	methodmessage=getmethod(productid,serviceid,apiid,versionid,resourceid)
	if methodmessage["statusCode"] == 200:
		if methodmessage["body"] !=[]:
			for method in methodmessage["body"]:
				for action in actions:
					action["methodpath"]=action["methodpath"].replace("{","<")
					action["methodpath"]=action["methodpath"].replace("}",">")
					if action["methodpath"] == method["methodpath"] and action["methodtype"] == method["methodtype"]:
						actions.remove(action)
	else:
		return(methodmessage)
	autopoppulate={
			"resourceid":resourceid,
			"serviceid":serviceid,
			"versionid":versionid,
			"actions": actions
		}
	actionlist=[]
	for act in autopoppulate["actions"]:
		methodid = uniqid("meth")
		act["methodid"]=methodid
		act["methodpath"]=act["methodpath"].replace("{","<")
		act["methodpath"]=act["methodpath"].replace("}",">")
		if act["methodpath"]!="":
			apicallpath="/"+versionname+"/"+resource["resourcename"]+act["methodpath"]
		else:
			apicallpath="/"+versionname+"/"+resource["resourcename"]
		method={"Ref": methodid}
		resource["methods"].append(method)
		resstatus,resstatusmessage,res=datafile.write_s3_file(resourcepath,resource)
		if resstatus == "error":
			message={"statusCode":400,"errorMessage":res}
			return(message)
		methodpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+".json"
		full_code = consolidate_code(act,requirements)
		# act["import_code"]=act["import_code"].replace("METHODID",methodid)
		# act["import_code"]=act["import_code"].replace("METHODPATH",apicallpath)
		# act["function_code"]=act["function_code"].replace("METHODID",methodid)
		# act["function_code"]=act["function_code"].replace("METHODPATH",apicallpath)
		# act["main_code"]=act["main_code"].replace("METHODID",methodid)
		# act["main_code"]=act["main_code"].replace("METHODPATH",apicallpath)
		# act["type_code"]=act["type_code"].replace("METHODID",methodid)
		# act["type_code"]=act["type_code"].replace("METHODPATH",apicallpath)
		# codestring=act["import_code"]+"\n"+act["function_code"]+"\n"+act["main_code"]+"\n"+act["type_code"]
		codepath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/"+methodid+".py"
		codestatus,codestatusmessage,code=datafile.write_txt_file(codepath,codestring)
		if codestatus=="error":
			message={"statusCode":400,"errorMessage":code}
			return(message)
		requirement=act["requirements"]
		reqstring=""
		for i in requirement:
			reqstring=reqstring+i+"\n"
		# act["requirements"]=reqstring
		requirementpath="servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/methods/"+methodid+"/code/requirement.txt"
		requirementstatus,requirementstatusmessage,req=datafile.write_txt_file(requirementpath,reqstring)
		if requirementstatus == "error":
			message={"statusCode":400,"errorMessage":req}
			return(message)
		methstatus,methstatusmessage,methres=datafile.write_s3_file(methodpath,act)
		if methstatus == "error":
			message={"statusCode":400,"errorMessage":code}
			return(message)
		if methstatus == "success" and codestatus == "success" and requirementstatus == "success":
			actionlist.append(act)
	message={"statusCode": 200,"body": actionlist}
	return(message)
	
	
	