import logging
import json
import sys,requests
import boto3
from boto3 import session
import time,os, math, random, base64, pprint
import re
from kubernetes import client,config
from datetime import datetime

def get_resource_pod_status(namespace,labelstring,fieldstring):
    config.load_kube_config("/home/app/web/kubeconfig")
    api_instance=client.CoreV1Api()
    try:
        podlist=api_instance.list_namespaced_pod(namespace, label_selector=labelstring)
        if podlist.items == []:
            podstatus = "inprogress"
            Message = "Pod is creating"
        else:
            podphase=podlist.items[0].status.phase
            print(podphase)
            if podphase == "Pending":
                podstatus="inprogress"
                Message = "Pod status is inprogress"
            elif podphase == "Running":
                for container in podlist.items[0].status.container_statuses:
                    functionid=container.name
                    # print(container)
                    if container.ready == True and container.started == True and container.state.running != None:
                        podstatus="Running"
                        Message="Pod "+functionid+" is Running"
                        # print(functionstatus)
                    elif container.ready == False and container.started == False and container.state.terminated != None:
                        podstatus="Completed"
                        Message="Pod "+functionid+" is Completed"
                        # print(functionstatus)
                    elif container.state.waiting is not None:
                        if container.state.waiting.reason == "CrashLoopBackOff" and container.restart_count > 0:
                            Message=container.last_state.terminated.reason
                            podstatus="Error"
                        elif container.restart_count == 0 and container.state.waiting != None:
                            Message=container.state.waiting.reason
                            podstatus="Error"
                        elif container.restart_count == 0 and container.state.terminated != None:
                            Message=container.state.terminated.reason
                            podstatus="Error"
            elif podphase == "Succeeded":
                for container in podlist.items[0].status.container_statuses:
                    functionid=container.name
                    # print(container)
                    if container.ready == True and container.started == True and container.state.running != None:
                        podstatus="Running"
                        Message="Pod "+functionid+" is Running"
                        # print(functionstatus)
                    elif container.ready == False and container.started == False and container.state.terminated != None:
                        podstatus="Completed"
                        Message="Pod "+functionid+" is Completed"
                        # print(functionstatus)
            elif podphase == "Failed":
                for container in podlist.items[0].status.container_statuses:
                    functionid=container.name
                    functionstatus="Error"
                    if container.state.waiting is not None:
                        if container.state.waiting.reason == "CrashLoopBackOff" and container.restart_count > 0:
                            Message=container.last_state.terminated.reason
                            podstatus="Error"
                        elif container.restart_count == 0 and container.state.waiting != None:
                            Message=container.state.waiting.reason
                            podstatus="Error"
                        elif container.restart_count == 0 and container.state.terminated != None:
                            Message=container.state.terminated.reason
                            podstatus="Error"
                    # print(functionstatus,ErrorMessage,ErrorState)
            # print(functionstatus)
        print(podstatus)
        return(podstatus,Message)
    except Exception as e:
        status = "error"
        errormessage = str(e)
        return(status,errormessage)

def get_namespaced_replica_set(namespace,labelstring):
    config.load_kube_config("/home/app/web/kubeconfig")
    api_instance=client.AppsV1Api()
    replicalist=api_instance.list_namespaced_replica_set(namespace, label_selector=labelstring, pretty="true")
    try:
        if replicalist.items[0].status.ready_replicas == 1:
            rsstatus = "Running"
            rsmessage = "Replica set is ready"
        else:
            rsstatus = "Error"
            rsmessage = "Replica set is got into error"
    except Exception as e:
        rsstatus = "Error"
        rsmessage = str(e)
    return(rsstatus,rsmessage)

def get_deployment_status(namespace,fieldstring):
    config.load_kube_config("/home/app/web/kubeconfig")
    api_instance=client.AppsV1Api()
    try:
        deploylist = api_instance.list_namespaced_deployment(namespace, field_selector=fieldstring)
        deployname = deploylist.items[0].metadata.name
        if deploylist.items[0].status.ready_replicas == 1:
            deploystatus = "Running"
            deploymessage = "deployment "+deployname+" is running"
        else:
            deploystatus = "Error"
            deploymessage = "deployment "+deployname+" is got into error"
        # print(deploystatus)
    except Exception as e:
        deploystatus = "Error"
        deploymessage = str(e)
    return(deploystatus,deploymessage)

def get_service_status(namespace,fieldstring):
  config.load_kube_config("/home/app/web/kubeconfig")
  api_instance=client.CoreV1Api()
  try:
    servicelist=api_instance.list_namespaced_service(namespace,field_selector=fieldstring)
    endpointlist=api_instance.list_namespaced_endpoints(namespace,field_selector=fieldstring)
    if servicelist.items[0].spec.cluster_ip != None and endpointlist.items[0].subsets[0].addresses[0].ip != None:
      servicestatus="Running"
      servicemessage="Service created successfully"
    else:
      servicestatus="Error"
      servicemessage="Service creation failed"
    return(servicestatus,servicemessage)
  except Exception as e:
    servicestatus="Error"
    servicemessage=str(e)
    return(servicestatus,servicemessage)