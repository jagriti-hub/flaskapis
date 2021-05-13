from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json
import datafile

logger=logging.getLogger() 
data_api = Blueprint('data_api', __name__)

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

@data_api.route('/design/v1/data/<serviceid>/<versionid>/<resourceid>', methods=['POST'])
def createdb(serviceid,versionid,resourceid):
    json_dict=request.get_json()
    resourcepath= "servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
    status,statusmessage,resource=datafile.load_s3_file(resourcepath)
    if status == "success":
        for data in resource["data"]:
            if data["db"] == []:
                dbid = uniqid("db")
                db = {"Ref": dbid}
                data["db"].append(db)
            elif data["db"] != []:
                dbids=[]
                for db in data["db"]:
                    dbids.append(db["Ref"])
                a= True
                while a is True:
                    dbid=uniqid('db')
                    if dbid in dbids:
                        a= True
                    else :
                        a= False
                db={"Ref": dbid}
                data["db"].append(db)
        resstatus,resstatusmessage,res=datafile.write_s3_file(resourcepath,resource)
        dbjson = {
                    "dbid": dbid,
                    "CreateType": "IMPORT|NEW",
                    "import": {
                            "Ref": dbid
                    },
                    "DBType": "DYNAMODB",
                    "type": "dynamodb",
                    "deploy": {
                        "type": "mock"
                    },
                    "tables": []
            }
        if "description" in json_dict:
            dbjson["description"]=request.json["description"]
        datapath= "servicedesigns/"+serviceid+"/data/"+dbid+"/config.json"
        status,statusmessage,response=datafile.write_s3_file(datapath,dbjson)
        if status == "success":
            message={"statusCode":200,"body":dbjson}
        else:
            message={"statusCode":400,"errorMessage":statusmessage}
    else:
        message={"errorMessage":statusmessage,"Error":resource}
    return(message)

@data_api.route("/design/v1/data/<serviceid>/<versionid>/<resourceid>/database", methods=["GET"])
def getdata(serviceid,versionid,resourceid):
    resourcepath= "servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
    status,statusmessage,resource=datafile.load_s3_file(resourcepath)
    if status == "success":
        for data in resource["data"]:
            database=[]
            if data["db"] != []:
                for db in data["db"]:
                    dbid=db["Ref"]
                    datapath= "servicedesigns/"+serviceid+"/data/"+dbid+"/config.json"
                    status,statusmessage,data=datafile.load_s3_file(datapath)
                    database.append(data)
                message={"statusCode":200,"body":database}
            else:
                message={"statusCode":200,"body":database}
    else:
        message={"errorMessage":statusmessage,"Error":resource}
    return(message)

@data_api.route("/design/v1/data/<serviceid>/<versionid>/<resourceid>/database/<dbid>", methods=["GET"])
def getdatabyid(serviceid,versionid,resourceid,dbid):
	datapath="servicedesigns/"+serviceid+"/data/"+dbid+"/config.json"
	status,statusmessage,data=datafile.load_s3_file(datapath)
	if status == "success":
		message={"statusCode":200,"body":data}
	else:
		message={"errorMessage":statusmessage,"Error":data}
	return(message)

@data_api.route('/design/v1/data/<serviceid>/<versionid>/<resourceid>/database/<dbid>', methods=['DELETE'])
def deletedata(serviceid,versionid,resourceid,dbid):
    resourcepath= "servicedesigns/"+serviceid+"/api/"+versionid+"/resources/"+resourceid+"/config.json"
    status,statusmessage,resource=datafile.load_s3_file(resourcepath)
    if status == "success":
        for data in resource["data"]:
            if data["db"] != []:
                dbids=[]
                for db in data["db"]:
                    dbids.append(db["Ref"])
                if dbid in dbids:
                    for db in data["db"]:
                        if db["Ref"]==dbid:
                            data["db"].remove(db)
                            status,statusmessage,response = datafile.write_s3_file(resourcepath,resource)
                    datapath="servicedesigns/"+serviceid+"/data/"+dbid+"/config.json"
                    delstatus,delstatusmessage,delres=datafile.delete_s3_file(datapath)
                    datapathprefix="servicedesigns/"+serviceid+"/data/"+dbid
                    delstatus,delstatusmessage=datafile.delete_folders(datapathprefix)
                    message={"statusCode":200,"message":"database deleted"}
                else:
                    message={"statusCode":400,"errorMessage":"dbid does not exist"}
            else:
                message={"statusCode": 400, "errorMessage":"no database present"}
    else:
        message={"errorMessage":statusmessage,"Error":resource}
    return(message)