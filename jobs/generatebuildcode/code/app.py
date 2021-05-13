import os,sys,time,logging,json,random,math
import pprint,base64,re,requests
from datetime import datetime
import boto3
from boto3 import session
import docker
import jsonpickle
import kubernetes
from kubernetes import client, config

import generatebuildcode
import s3files
import ecrdocker
import resourcedeployment
import getdeploymentstatus

serviceid=sys.argv[1]
versionid=sys.argv[2]
resourceid=sys.argv[3]
versionname = sys.argv[4]
namespace = sys.argv[5]

config.load_kube_config("/home/app/web/kubeconfig")
# config.load_kube_config("/home/ubuntu/.kube/config")
labelstring='resourceid='+resourceid
fieldstring='metadata.name='+resourceid

def main():
    timeout_counter_value = 50
    portnumber = "5000"
    resource_path = "servicedesigns"+"/"+serviceid+"/api/"+versionid+"/resources/"+resourceid
    resource_configfile = resource_path+"/config.json"
    method_path = resource_path + "/methods"
    print("METHODPATH:", method_path)
    status,status_message,resourceconfig=s3files.load_config_file(resource_configfile)
    if status == "success":
        dbid=resourceconfig["data"][0]["db"][0]["Ref"]
    else:
        dbid=""
    print("initial statsu:",status)
    print("initial load config: ",status_message)
    print("RESOURCECONFIG: ", resourceconfig)
    if status == "error":
        return(status,status_message,resourceconfig)
    resourcename = resourceconfig['resourcename']
    print("RESOURCECONFIGname: ", resourcename)

    blueprints = []
    import_module_app = []
    requirement_txt = []
    for method in resourceconfig["methods"]:
        methodid = method['Ref']
        methodid_path = method_path+"/"+methodid+"/code/"+methodid+".py"
        requirement_file_path = method_path+"/"+methodid+"/code/"+"requirement.txt"
        code_path = method_path
        code_gen_status,code_gen_status_message,methodid_code = generatebuildcode.build_code_generate(code_path,resourceid,methodid,method_path,dbid)
        print(code_gen_status_message)
        print(methodid_code)
        if code_gen_status == "error":
            return(code_gen_status,code_gen_status_message,methodid_code)

        status,statusmessage,response=s3files.func_output("Initiated",code_gen_status,"build_code_generate_initiated",code_gen_status_message,methodid_code,resource_path)
        if status == "error":
            return(status,statusmessage,response)
        status,statusmessage,load_requirement = s3files.load_requirement_file(requirement_file_path)
        print(load_requirement)
        if status == "error":
            return(status,statusmessage,load_requirement)
        requirement_txt.append(load_requirement)
        
        import_blueprint_form = 'from '+methodid+' import '+methodid
        import_module_app.append(import_blueprint_form)
        blueprint_form = "app.register_blueprint("+methodid+")"
        blueprints.append(blueprint_form)
    
    generate_requirement_status,generate_requirement_statusmessage,generate_requirement_file = generatebuildcode.generate_requirement_file(resourceid,requirement_txt)
    print("generate_requirement_statusmessage: ", generate_requirement_statusmessage)
    if generate_requirement_status == "error":
        return(generate_requirement_status,generate_requirement_statusmessage,generate_requirement_file)

    generate_app_py_status,generate_app_py_statusmessage,app_py_create = generatebuildcode.generate_app_python_file(resourceid,blueprints,import_module_app)
    print("generate_app_py_statusmessage: ", generate_app_py_statusmessage)
    if generate_app_py_status == "error":
        return(generate_app_py_status,generate_app_py_statusmessage,app_py_create)
    
    generate_docker_status,generate_docker_statusmessage,docker_file_create = generatebuildcode.generate_docker_file(resourceid)
    print("generate_docker_statusmessage: ",generate_docker_statusmessage)
    if generate_docker_status == "error":
        return(generate_docker_status,generate_docker_statusmessage,docker_file_create)
    
    imagename = resourceid
    buildtag = "latest"
    dockerhost = "localhost:32000/"
    build_path = "./"+resourceid+"/"
    
    build_status,build_status_message,build_image_output = ecrdocker.docker_build(imagename,buildtag,dockerhost,build_path)
    print("build_status_message: ", build_status_message)
    print("messgae ",build_image_output)
    if build_status == "error":
        return(build_status,build_status_message,build_image_output)

    status,statusmessage,response=s3files.write_output_file(resource_path+"/buildlog.json",build_image_output)
    if status == "error":
        return(status,statusmessage,response)
    imagetags = build_image_output["imagetag"]
    
    imagetags = build_image_output["imagetag"]

    push_status,push_status_message,pushoutput = ecrdocker.docker_push(imagetags)
    print("push_status_message: ", push_status_message)
    if push_status == "error":
        return(push_status,push_status_message,pushoutput)
    
    status,statusmessage,response=s3files.write_output_file(resource_path+"/pushlog.json",pushoutput)
    if status == "error":
        return(status,statusmessage,response)
    imagetags = build_image_output["imagetag"]
    
    imageendpoint = dockerhost + imagetags + ':' + buildtag

    if build_status == "success" and push_status == "success":
        deploy_status,deploy_status_message,deploy_response = resourcedeployment.resource_deploy(namespace,resourceid,serviceid,versionid,resourcename,versionname,dockerhost,imagename,buildtag,portnumber)
        print("deploy_status_message: ", deploy_status_message)
        if deploy_status == "error":
            return(deploy_status,deploy_status_message,deploy_response)

        pod_inprogress=True
        timeout_counter = 0
        while pod_inprogress:
            podstatus,podmessage=getdeploymentstatus.get_resource_pod_status(namespace,labelstring,fieldstring)
            pod_status_data={
            "podstatus": podstatus,
            "podmessage": podmessage,
            "resourceid": resourceid
            }
            if pod_status_data["podstatus"] != "inprogress":
                pod_inprogress = False     
            if timeout_counter >= timeout_counter_value:
                pod_inprogress = False
            timeout_counter = timeout_counter + 1
            time.sleep(30)
        
        if pod_status_data["podstatus"] in ["Running","Completed"]:
            time.sleep(20)
            replicasetstatus,replicasetmessage=getdeploymentstatus.get_namespaced_replica_set(namespace,labelstring)
            if replicasetstatus == "Running":
                deploymentstatus,deploymentmessage=getdeploymentstatus.get_deployment_status(namespace,fieldstring)
                if deploymentstatus == "Running":
                    servicestatus,servicemessage=getdeploymentstatus.get_service_status(namespace,fieldstring)
                    if servicestatus == "Running":
                        ingressstatus,ingressmessage=getdeploymentstatus.get_ingress_status(namespace,fieldstring)
                        if ingressstatus == "Running":
                            status,statusmessage,response=s3files.func_output("Running",ingressstatus,"Getting_Ingress_Status",ingressmessage,"success",resource_path)
                            if status == "error":
                                return(status,statusmessage,response)
                        else:
                            status,statusmessage,response=s3files.func_output("Error",ingressstatus,"Getting_Ingress_Status",ingressmessage,"Ingress_Failed",resource_path)
                            if status == "error":
                                return(status,statusmessage,response)
                    else:
                        status,statusmessage,response=s3files.func_output("Error",servicestatus,"Getting_Service_Status",servicemessage,"Service_Failed",resource_path)
                        if status == "error":
                            return(status,statusmessage,response)
                else:
                    status,statusmessage,response=s3files.func_output("Error",deploymentstatus,"Getting_Deployemnt_Status",deploymentmessage,"Deployment_Failed",resource_path)
                    if status == "error":
                        return(status,statusmessage,response)
            else:
                status,statusmessage,response=s3files.func_output("Error",replicasetstatus,"Getting_Replicaset_Status",replicasetmessage,"Replicaset_Failed",resource_path)
                if status == "error":
                    return(status,statusmessage,response)
        else:
            status,statusmessage,response=s3files.func_output("Error",pod_status_data["podstatus"],"Getting_Pod_Status",pod_status_data["podmessage"],"Pod_Failed",resource_path)
            if status == "error":
                return(status,statusmessage,response)

main()