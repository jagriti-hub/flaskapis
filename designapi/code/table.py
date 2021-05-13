from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json
import datafile

logger=logging.getLogger()
table_api = Blueprint('table_api', __name__)

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

@table_api.route('/design/v1/table/<serviceid>/<dbid>', methods=['POST'])
def createtable(serviceid,dbid):
    iop={
        "tablename":""
    }
    tablename=request.json["tablename"]
    json_dict=request.get_json()
    dbpath= "servicedesigns/"+serviceid+"/data/"+dbid+"/config.json"
    status,statusmessage,database=datafile.load_s3_file(dbpath)
    if status == "success":
        if database["tables"] == []:
            tableid=uniqid("tb")
        elif database["tables"] != []:
            a= True
            while a is True:
                tableid=uniqid('tb')
                if tableid in database["tables"]:
                    a= True
                else :
                    a= False
        database["tables"].append(tableid)
        status,statusmessage,response=datafile.write_s3_file(dbpath,database)
        tablejson={
            "tableid": tableid,
            "tablename":tablename,
            "dbtype":database["DBType"],
            "schema": [],
            "indexes": {}
        }
        if "description" in json_dict:
            tablejson["description"]=request.json["description"]
        tablepath="servicedesigns/"+serviceid+"/data/"+dbid+"/tables/"+tableid+"/config.json"
        status,statusmessage,table=datafile.write_s3_file(tablepath,tablejson)
        if status == "success":
            message={"statusCode":200,"message":"Table Created","body":tablejson}
        else:
            message={"statusCode":400,"errorMessage":statusmessage,"Error":table}
    else:
        message={"statusCode":400,"errorMessage":statusmessage,"Error":database}
    return(message)

@table_api.route('/design/v1/table/<serviceid>/<dbid>/<tableid>', methods=['PATCH'])
def updatetable(serviceid,dbid,tableid):
    json_dict=request.get_json()
    tablepath= "servicedesigns/"+serviceid+"/data/"+dbid+"/tables/"+tableid+"/config.json"
    status,statusmessage,table=datafile.load_s3_file(tablepath)
    if status == "success":
        if "addschema" in json_dict:
            for sch in request.json['addschema']:
                if all(sch['attributename'] != tbh['attributename'] for tbh in table['schema']):
                    table['schema'].append(sch)
            # table['schema']=table['schema']+request['addschema']
        if "deleteschema" in json_dict:
            for sch in request.json['deleteschema']:
                for schema in table['schema']:
                    if sch['attributename'] == schema['attributename']:
                        if sch['attributename'] not in str(table['indexes']):
                            table['schema'].remove(schema)
        if "editschema" in json_dict:
            for schema in table['schema']:
                for sch in request.json['editschema']:
                    if sch['attributename'] == schema['attributename']:
                        table['schema'][table['schema'].index(schema)]=sch
        if "indexes" in json_dict:
            table['indexes']=request.json['indexes']
        if "updatepath" in json_dict:
            request.json['updatevalue']=json.loads(request.json['updatevalue'])
            path=request.json['updatepath'].split("/")
            myd=table
            for i in path[:-1]:
                myd=myd[i]
            if "[" in path[-1]:
                path[-1]=path[-1].replace("]","")
                p=path[-1].split("[")
                if p[0] not in myd:
                    myd[p[0]]=[]
                if int(p[1]) >= len(myd[p[0]]):
                    myd[p[0]].append(request.json['updatevalue'])
                else:
                    myd[p[0]][int(p[1])]=request.json['updatevalue']
            else:
                myd[path[-1]]=request.json['updatevalue']
        status,statusmessage,response=datafile.write_s3_file(tablepath,table)
        if status == "success":
            message={"statusCode":200,"body":table}
        else:
            message={"statusCode":400,"errorMessage":statusmessage}
    else:
        message={"errorMessage":statusmessage,"Error":table}
    return(message)


@table_api.route('/design/v1/table/<serviceid>/<dbid>', methods=['GET'])
def gettable(serviceid,dbid):
    dbpath= "servicedesigns/"+serviceid+"/data/"+dbid+"/config.json"
    status,statusmessage,data=datafile.load_s3_file(dbpath)
    if status == "success":
        tables=[]
        if data["tables"] != []:
            for tableid in data["tables"]:
                tablepath="servicedesigns/"+serviceid+"/data/"+dbid+"/tables/"+tableid+"/config.json"
                status,statusmessage,table=datafile.load_s3_file(tablepath)
                tables.append(table)
            message={"statusCode":200,"body":tables}
        else:
            message={"statusCode":200,"body":tables}
    else:
        message={"errorMessage":statusmessage,"Error":data}
    return(message)

@table_api.route('/design/v1/table/<serviceid>/<dbid>/<tableid>', methods=['GET'])
def gettablebyid(serviceid,dbid,tableid):
    tablepath="servicedesigns/"+serviceid+"/data/"+dbid+"/tables/"+tableid+"/config.json"
    status,statusmessage,table=datafile.load_s3_file(tablepath)
    if status == "success":
        message={"statusCode":200,"body":table}
    else:
        message={"errorMessage":statusmessage,"Error":table}
    return(message)

@table_api.route('/design/v1/table/<serviceid>/<dbid>/<tableid>', methods=['DELETE'])
def deletetable(serviceid,dbid,tableid):
    dbpath= "servicedesigns/"+serviceid+"/data/"+dbid+"/config.json"
    status,statusmessage,data=datafile.load_s3_file(dbpath)
    if status == "success":
        if tableid in data["tables"]:
            tablepathprefix="servicedesigns/"+serviceid+"/data/"+dbid+"/tables/"+tableid
            data["tables"].remove(tableid)
            status,statusmessage=datafile.delete_folders(tablepathprefix)
            datastatus,datamessage,datawrite=datafile.write_s3_file(dbpath,data)
            if status == "success":
                message={"statusCode":200,"message":"Table Deleted"}
            else:
                message={"statusCode":400,"errorMessage":"Table deletion failed"}
        else:
            message={"statusCode":400,"errorMessage":"tableid does not exist"}
    else:
        message={"errorMessage":statusmessage,"Error":data}
    return(message)
        