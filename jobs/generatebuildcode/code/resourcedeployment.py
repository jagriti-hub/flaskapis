import logging
import os,time,random,math
import json
import sys
import boto3
from boto3 import session
import kubernetes
import docker
import jsonpickle
from datetime import datetime
from kubernetes import client, config

def create_deployment(api_instance,namespacename,dockerhost,imagename,buildtag,resourceid,portnumber):
  try:
    container =[] 
    imagetag=dockerhost+imagename+":"+buildtag
    containerdef={
        "name": resourceid,
        "image": imagetag,
        "ports": [client.V1ContainerPort(container_port=int(portnumber))]
      }
    container = []
    containeritem = client.V1Container( **containerdef )
    container.append(containeritem)
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={'resourceid': resourceid}),
        spec=client.V1PodSpec(containers=container))
    # Create the specification of deployment
    spec = client.V1DeploymentSpec(
        replicas=1,
        template=template,
        selector={'matchLabels': {'resourceid': resourceid}})
    # Instantiate the deployment object
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=resourceid),
        spec=spec)
    api_response = api_instance.create_namespaced_deployment(
      body=deployment,
      namespace=namespacename)
    return("success", "Deployment_Intiated", api_response)
  except Exception as Error:
    return("error", "Deployment_Intiation_Failed", Error)
      
def create_service(api_instance,namespacename,resourceid,portnumber):
  try:
    body = client.V1Service(
          metadata=client.V1ObjectMeta(
          name=resourceid
        ),
        spec=client.V1ServiceSpec(
            selector={'resourceid': resourceid},
            ports=[client.V1ServicePort(
                port=80,
                target_port=int(portnumber)
            )]
        )
    )
    api_response = api_instance.create_namespaced_service(namespace=namespacename, body=body)
    return("success", "Service_Intiated", api_response)
  except Exception as Error:
    return("error", "Service_Intiation_Failed", str(Error))

def create_ingress(api_instance, namespacename, resourceendpoint,resourceurl,resourceid):
  try:
    body = client.NetworkingV1beta1Ingress(
        api_version="networking.k8s.io/v1beta1",
        kind="Ingress",
        metadata=client.V1ObjectMeta(name=resourceid, annotations={
            "nginx.ingress.kubernetes.io/rewrite-target": resourceurl
        }),
        spec=client.NetworkingV1beta1IngressSpec(
            rules=[client.NetworkingV1beta1IngressRule(
                http=client.NetworkingV1beta1HTTPIngressRuleValue(
                    paths=[client.NetworkingV1beta1HTTPIngressPath(
                        path=resourceendpoint,
                        backend=client.NetworkingV1beta1IngressBackend(
                            service_port=80,
                            service_name=resourceid)
                    )]
                )
            )
            ]
        )
    )
    # Creation of the Deployment in specified namespace
    # (Can replace "default" with a namespace you may have created)
    api_response = api_instance.create_namespaced_ingress(
        namespace=namespacename,
        body=body
    )
    return("success", "Ingress_Intiated", api_response)
  except Exception as Error:
    return("error", "Ingress_Intiation_Failed", str(Error))

def resource_deploy(namespace,resourceid,serviceid,versionid,resourcename,versionname,dockerhost,imagename,buildtag,portnumber): 
  # config.load_kube_config("/home/ubuntu/.kube/config")
  config.load_kube_config("/home/app/web/kubeconfig")
  try:
    api_instance=client.AppsV1Api()
    status,status_message,data = create_deployment(api_instance,namespace,dockerhost,imagename,buildtag,resourceid,portnumber)
    api_instancestatus = status
    print("api_instancestatus: ", api_instancestatus)
    print(status_message)
    print(data)
    if status == "success":
      api_instance=client.CoreV1Api()
      status,status_message,data = create_service(api_instance,namespace,resourceid,portnumber)
      createservicestatus = status
      print("createservicestatus: ", createservicestatus)
      if status == "success":
        api_instance=client.NetworkingV1beta1Api()
        resourceurl="/"+versionname+"/"+resourcename+'/$2'
        resourceendpoint="/liveapp/"+serviceid+"/"+versionname+"/"+resourcename+'(/|$)(.*)'
        status,status_message,data = create_ingress(api_instance,namespace,resourceendpoint,resourceurl,resourceid)
        create_ingress_status = status
        print("create_ingress_status: ", create_ingress_status)
      else:
        raise Exception(data)
    else:
      raise Exception(data)
  except Exception as Error:
    status= "error"
    status_message= "Error in Deployment",
    data= str(Error)
  return(status, status_message ,data)