import logging
import json
import sys
import boto3,requests
from boto3 import session
import time,os, math, random, base64, pprint
import re
from kubernetes import client,config
from datetime import datetime


def create_db_deployment(dbid,namespace,dbtype):
  try:
    config.load_kube_config("/home/app/web/kubeconfig")
  except Exception as e:
    return("error", "Loading_kubeconfigfile_failed", str(e))
  try:
    api_instance=client.AppsV1Api()
    if dbtype == "DYNAMODB":
      image = "amazon/dynamodb-local:1.13.6" 
      port = 8000
    containerdef={
        "name": dbid,
        "image": image,
        "ports": [client.V1ContainerPort(container_port=port)],
        "command": ["java","-jar","DynamoDBLocal.jar","-sharedDb","-optimizeDbBeforeStartup","-dbPath","./"]
      }
    container = []
    containeritem = client.V1Container( **containerdef )
    container.append(containeritem)
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={'dbid': dbid}),
        spec=client.V1PodSpec(containers=container))
    # Create the specification of deployment
    spec = client.V1DeploymentSpec(
        replicas=1,
        template=template,
        selector={'matchLabels': {'dbid': dbid}})
    # Instantiate the deployment object
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=dbid),
        spec=spec)
    api_response = api_instance.create_namespaced_deployment(
      body=deployment,
      namespace=namespace)
    return("success", "Deployment_Intiated", api_response)
  except Exception as Error:
    print(str(Error))
    return("error", "Deployment_Intiation_Failed", str(Error))
    
def create_db_service(dbid,namespacename):
  try:
    config.load_kube_config("/home/app/web/kubeconfig")
    api_instance=client.CoreV1Api()
    body = client.V1Service(
          metadata=client.V1ObjectMeta(
          name=dbid
        ),
        spec=client.V1ServiceSpec(
            selector={'dbid': dbid},
            ports=[client.V1ServicePort(
                port=80,
                target_port=8000
            )]
        )
    )
    api_response = api_instance.create_namespaced_service(namespace=namespacename, body=body)
    return("success", "Service_Intiated", api_response)
  except Exception as Error:
    return("error", "Service_Intiation_Failed", str(Error))