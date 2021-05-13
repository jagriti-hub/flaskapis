import logging
import json
import sys,requests
import boto3
from boto3 import session
import time,os, math, random, base64, pprint
import re
from kubernetes import client,config
from datetime import datetime

import s3files
import databasedeployment
import getstatus

db_path = sys.argv[1]
dbid = sys.argv[2]
dbtype = sys.argv[3]


def main():
  timeout_counter_value = 50
  namespace = "default"
  db_outputfile=db_path+"/output.json"
  db_logfile=db_path+"/log.json"
  db_configfile=db_path+"/config.json"
  deployment_status,deployment_status_message,deployment_data = databasedeployment.create_db_deployment(dbid,namespace,dbtype)
  service_status,service_status_message,servive_data = databasedeployment.create_db_service(dbid,namespace)
  print(deployment_status)
  print(service_status)
  print("start checking")
  labelstring='dbid='+dbid
  fieldstring='metadata.name='+dbid
  datapod_status_check = True
  timeout_counter =0
  while datapod_status_check:
    datapod_status,datapod_statusmessage= getstatus.get_resource_pod_status(namespace,labelstring,fieldstring)
    if datapod_status != "inprogress":
      datapod_status_check = False
    if timeout_counter >= timeout_counter_value:
      datapod_status_check = False
      timeout_counter = timeout_counter + 1
      time.sleep(5)
    print(datapod_status)
  print("datapodstatus: ",datapod_status)
  print(datapod_statusmessage)
  time.sleep(20)
  if datapod_status == "Running":
    rsstatus,rsstatusmessage = getstatus.get_namespaced_replica_set(namespace,labelstring)
    if rsstatus == "Running":
      deploystatus,deploymessage=getstatus.get_deployment_status(namespace,fieldstring)
      print(deploystatus)
      if deploystatus == "Running":
        output={
          "status": "Initiated",
          "Running": None,
          "Error": None,
          "Initiated": {
            "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
            "step": "db_deployment_creation_status",
            "status": deploystatus,
            "status_message": deploymessage
          },
          "Degraded": None
        }
        status,status_message,dbinput_config=s3files.load_config_file(db_configfile)
        if status == "error":
          return(status,status_message,dbinput_config)
        db_output_state={"state": output}
        dbinput_config.update(db_output_state)
        status,statusmessage,response=s3files.write_output_file(db_outputfile,dbinput_config)
        if status == "error":
          return(status,statusmessage,response)
        status,statusmessage,response=s3files.write_log_file(db_logfile,output)
        if status == "error":
          return(status,statusmessage,response)
        servicestatus,servicemessage=getstatus.get_service_status(namespace,fieldstring)
        if servicestatus == "Running":
          output={
            "status": "Running",
            "Initiated": None,
            "Error": None,
            "Running": {
              "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
              "step": "db_container_status",
              "status": "success",
              "status_message": "DB_CONTAINER_RUNNING_SUCCESSFULLY"
            },
            "Degraded": None
          }
        else:
          output={
            "status": "Error",
            "Degraded": None,
            "Initiated": None,
            "Running": None,
            "Error": {
              "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
              "step": "db_service_creation_status",
              "status": servicestatus,
              "status_message": servicemessage,
            }
          }
      elif deploystatus == "Error":
        output={
          "status": "Error",
          "Degraded": None,
          "Initiated": None,
          "Running": None,
          "Error": {
            "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
            "step": "db_deployment_creation_status",
            "status": deploystatus,
            "status_message": deploymessage,
          }
        }
    else:
      output={
          "status": "Error",
          "Error": {
            "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
            "step": "replicaset_creation_status",
            "status": rsstatus,
            "status_message": rsstatusmessage,
          },
          "Initiated": None,
          "Running": None,
          "Degraded": None
        }
  else:
    output={
        "status": "Error",
        "Error": {
          "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
          "step": "db_pod_creation_status",
          "status": datapod_status,
          "status_message": datapod_statusmessage,
        },
        "Initiated": None,
        "Running": None,
        "Degraded": None
      }
  status,status_message,dbinput_config=s3files.load_config_file( db_configfile)
  if status == "error":
    return(status,status_message,dbinput_config)
  db_output_state={"state": output}
  dbinput_config.update(db_output_state)
  status,statusmessage,response=s3files.write_output_file(db_outputfile,dbinput_config)
  if status == "error":
    return(status,statusmessage,response)
  status,statusmessage,response=s3files.write_log_file(db_logfile,output)
  if status == "error":
    return(status,statusmessage,response)
  print("deployment_status: ",output)
  return("success","DBCONTAINER_DEPLOYED","success")

FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.ERROR)
status,statusmessage,response=main()
if status == "error":
  logging.error(statusmessage+"-"+str(response))
if status == "success":
  logging.info(statusmessage+"-"+str(response))