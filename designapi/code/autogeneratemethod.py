from flask import Flask, jsonify
from flask import Blueprint
from flask import request,json
import boto3,time,math,random,os
import logging,json
from boto3.dynamodb.conditions import Key, Attr

logger=logging.getLogger()
autogeneratemethod_api = Blueprint('autogeneratemethod_api', __name__)

path = "/home/app/web/archeplay/template"

def load_s3_file(filepath):
	path=filepath
	if os.path.exists(path):
		file_object=open(path,"r")
		datastring=file_object.read()
		data=json.loads(datastring)
		successmessage=filepath+" loaded Successfully"
		return("success", successmessage, data)
	else:
		errormessage=filepath+" not found"
		Error="file does not exist"
		return("error", errormessage, str(Error))

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
    return(uniqid)

def dynamodb_type(tablename,indexes,schema,tableid):
    table={}
    table['TABLENAME']=tablename
    table['tableid'] = tableid
    table['PRIMARYKEY']=indexes['primary']['key']
    if "sortkey" in indexes['primary'] and indexes['primary']['sortkey']!="":
        table['SORTKEY']=indexes['primary']['sortkey']
    table['secondary']=[]
    if "secondary" not in indexes:
        indexes['secondary']=[]
    for sec in indexes['secondary']:
        s={
            "indexname":sec['indexname'],
            "PRIMARYKEY":sec['key']
        }
        if sec['sortkey']!="":
            s['SORTKEY']=sec['sortkey']
        table['secondary'].append(s)
    return table

def re_code(template,table,cde):
    for k in template['replacevariables']:
        if k in table:
            cde=cde.replace(k,table[k])
    return cde

def create_actions(table,template,dbid):
    action={
        "methodpath":template['methodpath'],
        "methodtype":template['methodtype'],
        "language":template['language'],
        "snippets": {},
        "keys": template["keys"],
        "dbtype": template["dbtype"],
        "primarykey": table["PRIMARYKEY"],
        "type_code": template["type_code"],
        "datasource":{
            "db": {
                "tableid" :table["tableid"],
                "dbid": dbid
            }
        },
        "servicetype": template["servicetype"]
    }
    if "TABLENAME" in action['methodpath']:
        action['methodpath']=action['methodpath'].replace('TABLENAME',table['TABLENAME'])
    if "PRIMARYKEY" in action["type_code"]:
        action["type_code"]=action["type_code"].replace('PRIMARYKEY',table['PRIMARYKEY'])
    if "SORTKEY" in action["type_code"]:
        action["type_code"]=action["type_code"].replace('SORTKEY',table['SORTKEY'])
    for snippet in template["snippets"]["snippetorder"]:
        snippetid = snippet["snippetid"]
        snippet_data = {
            "import_code": "",
            "function_code": "",
            "function_call": "",
            "data_code": "",
            "requirements": template["snippets"][snippetid]["requirements"],
            "version": template["snippets"][snippetid]["version"],
            "name": template["snippets"][snippetid]["name"],
            "snippetid": snippetid
        }
        if 'SORTKEY' in table:
            action.update({"sortkey": table["SORTKEY"]})
        for k in template["snippets"][snippetid]['replacevariables']:
            if k in table:
                action['methodpath']=action['methodpath'].replace(k,table[k])
        cd_tem=["import_code","function_code","function_call","data_code"]
        for cd in cd_tem:
            if cd in template["snippets"][snippetid]:
                snippet_data[cd]=re_code(template["snippets"][snippetid],table,template["snippets"][snippetid][cd])
        action["snippets"].update({snippetid: snippet_data})
        snippetorder = template["snippets"]["snippetorder"]
        action_snippets = {
            "snippets":{
                snippetid : snippet_data,
                "snippetorder": snippetorder
            }
        }
        action.update(action_snippets)
    # testcase_output = [] 
    # for testcase in template["testcase"]:
    #     testcaseid = testcase["testcaseid"]
    #     testcase_data = {
    #         "body": testcase["body"],
    #         "pathparameters" : testcase["pathparameters"],
    #         "queryparameters": testcase["queryparameters"],
    #         "headers": testcase["headers"],
    #         "testcasename": testcase["testcasename"],
    #         "testcaseid": testcaseid
    #     }
    #     if "PRIMARYKEY" in testcase_data["body"]:
    #         testcase_data["body"] = testcase_data["body"].replace("PRIMARYKEY",table["PRIMARYKEY"])
    #     if "SORTKEY" in testcase_data["body"]:
    #         testcase_data["body"] = testcase_data["body"].replace("SORTKEY",table["SORTKEY"])
    #     count = 0
    #     for item in testcase["pathparameters"]:
    #         if "PRIMARYKEY" in testcase["pathparameters"]:
    #             testcase_data["pathparameters"][count] = testcase_data["pathparameters"][count].replace("PRIMARYKEY",table["PRIMARYKEY"])
    #         if "SORTKEY" in testcase["pathparameters"]:
    #             testcase_data["pathparameters"][count] = testcase_data["pathparameters"][count].replace("SORTKEY",table["SORTKEY"])
    #         count = count +1
    #     testcase_output.append(testcase_data)
    # action.update({"testcase": testcase_output})
    return action
    
def create_template(templates,dbtype):
    data = []
    snippets = []
    snippetpath = path + "/snippets"
    dirs = os.listdir( snippetpath )
    for files in dirs:
        status,status_message,snippetjson = load_s3_file(snippetpath + "/" + files)
        if status == "error":
            message={"statusCode": 400, "errorMessage": str(snippetjson)}
            return(message)
        snippets.append(snippetjson)
    final_templates_output=[]
    for template in templates:
        final_template=template
        combine_snippet = {}
        snippet_order_output = {}
        snippet_order=[]
        for snippet in snippets:
            if snippet["keys"] == template["keys"] and snippet["methodtype"] == template["methodtype"] and snippet["methodpath"] == template["methodpath"]:
                snippetid = uniqid("sn_")
                snippet["function_call"] = snippet["function_call"].replace("SNIPPETID",snippetid)
                snippet["function_code"] = snippet["function_code"].replace("SNIPPETID",snippetid)
                snippet["snippetid"] = snippetid 
                snippet_order_output={
                    "name" : snippet["name"],
                    "snippetid": snippetid 
                }
                snippet_order.append(snippet_order_output)
                combine_snippet[snippetid]= snippet
        final_template["snippets"].update(combine_snippet)
        final_template["snippets"].update({"snippetorder": snippet_order})
        final_templates_output.append(final_template)
    return(final_templates_output)    

def dynamodb_actions(table,templates,dbid):
    actions=[]
    for template in templates:
        if "SORTKEY" in table and table['SORTKEY']!="":
            if template['keys'] == "primary_sort":
                action=create_actions(table,template,dbid)
                actions.append(action)
        elif "PRIMARYKEY" in table and table['PRIMARYKEY']!="":
            if template['keys'] == "primary":
                action=create_actions(table,template,dbid)
                actions.append(action)
    return actions

def snippet_actions(templates,dbtype,keys):
    actions=[]
    for template in templates:
        if template['keys'] == keys and template["dbtype"] == dbtype:
            actions.append(template)
    return actions

@autogeneratemethod_api.route('/design/v1/api/snippetmethods', methods=['POST'])   
def autogenerate_method():
    # TODO implement
    # event={
    #     "dbtype": "dynamodb",
    #     "servicetype":"dynamodb_eks_flask",
    #     "tablename":"studentdetails",
    #     "indexes": {
    #         "primary":{
    #             "key": "id",
    #             "sortkey": "name"
    #         }
    #     },
    #     "schema": {},
    #     "tableid": "tb1234",
    #     "dbid": "db1234"
    # }  
    sample_ip={
        "dbtype": "",
        "servicetype":"",
        "tablename":"",
        "indexes":"",
        "tableid": "",
        "dbid": ""
    }
    dbtype = request.json["dbtype"]
    data = []
    templates = []
    methodpath=path + "/methods"
    dirs = os.listdir( methodpath )
    for files in dirs:
        status,status_message,methodjson = load_s3_file(methodpath + "/" + files)
        if status == "error":
            message={"statusCode": 400, "errorMessage": str(status_message)}
            return(message)
        if methodjson["dbtype"] == request.json["dbtype"]:
            templates.append(methodjson)
    # print(templates)
    table=dynamodb_type(request.json['tablename'],request.json['indexes'],request.json['schema'],request.json['tableid'])
    templates=create_template(templates,dbtype)
    # return templates
    actions=dynamodb_actions(table,templates,request.json['dbid'])
    return {
        'statusCode': 200,
        'body': actions
    }

@autogeneratemethod_api.route('/design/v1/api/getallsnippet', methods=['POST'])   
def getall_snippets():
    # TODO implement
    sample_ip={
        "dbtype": "dynamodb",
        "servicetype":"dynamodb_eks_flask",
        "keys": "primary_sort"
    }
    data = []
    templates = []
    snippetpath=path + "/snippets"
    dirs = os.listdir( snippetpath )
    for files in dirs:
        status,status_message,snippetjson = load_s3_file(snippetpath + "/" + files)
        if status == "error":
            message={"statusCode": 400, "errorMessage": str(status_message)}
            return(message)
        if snippetjson["servicetype"] == request.json["servicetype"]:
            templates.append(snippetjson)
    actions = snippet_actions(templates,request.json['dbtype'],request.json['keys'])
    message = {"statusCode": 200, "body": actions}
    return(message)
