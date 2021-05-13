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

def get_job_status(namespace,fieldstring):
    api_instance=client.BatchV1Api()
    try:
        joblist=api_instance.list_namespaced_job(namespace,field_selector=fieldstring)
        jobname=joblist.items[0].metadata.name
        print(jobname)
        if joblist.items[0].status.active == 1:
            jobstatus = "inprogress"
            jobmessage= "Job "+jobname+" is inprogress"
        if joblist.items[0].status.active == None and joblist.items[0].status.succeeded == 1:
            jobstatus= "completed"
            jobmessage= "Job "+jobname+" is completed"
        elif joblist.items[0].status.active == None and joblist.items[0].status.failed == 1:
            jobstatus = "error"
            jobmessage = joblist.items[0].status.conditions.reason
        return(jobstatus,jobmessage)
    except Exception as e:
        jobstatus = "error"
        jobmessage = str(e)
        return(jobstatus,jobmessage)

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
    api_instance=client.AppsV1Api()
    replicalist=api_instance.list_namespaced_replica_set(namespace, label_selector=labelstring, pretty="true")
    try:
        if replicalist.items[0].status.ready_replicas == 1:
            rsstatus = "Running"
            rsmessage = "Replica set is ready"
        else:
            rsstatus = "Error"
            rsmessage = "Replica set is got into error"
        return(rsstatus,rsmessage)
    except Exception as e:
        rsstatus = "Error"
        rsmessage = str(e)
        return(rsstatus,rsmessage)

def get_deployment_status(namespace,fieldstring):
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
        print(deploystatus)
        return(deploystatus,deploymessage)
    except Exception as e:
        deploystatus = "Error"
        deploymessage = str(e)
        return(deploystatus,deploymessage)

def get_service_status(namespace,fieldstring):
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

def get_ingress_status(namespace,fieldstring):
  api_instance=client.NetworkingV1beta1Api()
  try:
    ingresslist=api_instance.list_namespaced_ingress(namespace, field_selector=fieldstring, pretty="true")
    if ingresslist.items[0].status.load_balancer.ingress[0].ip != None:
      ingressstatus = "Running"
      ingressmessage = "ingress is created"
    else:
      ingressstatus = "Error"
      ingressmessage = "ingress is not created"
    return(ingressstatus,ingressmessage)
  except Exception as e:
    ingressstatus= "Error"
    ingressmessage = str(e)
    return(ingressstatus,ingressmessage)