import logging
import json
import sys
import boto3,requests
from boto3 import session
import time,os, math, random, base64, pprint
import re
from kubernetes import client,config
from datetime import datetime


def load_config_file(bucket_name, configfilepath,connection):
  s3_client=connection.client('s3')
  try:
    s3_response=s3_client.get_object(Bucket=bucket_name,Key=configfilepath)
    config_file_object=s3_response["Body"].read()
    config=json.loads(config_file_object)
    status="success"
    successmessage=configfilepath+" loaded Successfully"
    return("success", successmessage, config)
  except Exception as Error:
    status="error"
    errormessage=configfilepath+"not loaded Successfully"
    return(status, errormessage, Error)
    
def write_output_file(bucket_name, outputfilepath, output,connection):
  try:
    s3_client=connection.client('s3')
    outputstring=json.dumps(output)
    s3_response=s3_client.put_object(Bucket=bucket_name,Key=outputfilepath,Body=outputstring)
    status="success"
    successmessage=outputfilepath+" written Successfully"
    return(status, successmessage, s3_response)
  except Exception as Error:
    status="error"
    errormessage=outputfilepath+" written Failed"
    return(status, errormessage, Error)
    
def write_log_file(bucket_name, logfilepath, log,connection):
  try:
    print(logfilepath)
    s3_client=connection.client('s3')
    s3_response=s3_client.get_object(Bucket=bucket_name,Key=logfilepath)
    print(s3_response)
    log_file_object=s3_response["Body"].read()
    logfile=json.loads(log_file_object)
    print(logfile)
    logfile["logs"].append(log)
    logstring=json.dumps(logfile)
    s3_response=s3_client.put_object(Bucket=bucket_name,Key=logfilepath,Body=logstring)
    status="success"
    successmessage=logfilepath+" written Successfully"
    return(status, successmessage, s3_response)
  except Exception as Error:
    if "NoSuchKey" in str(Error):
      try:
        logfile={
          "logs": []
        }
        logfile["logs"].append(log)
        logstring=json.dumps(logfile)
        s3_response=s3_client.put_object(Bucket=bucket_name,Key=logfilepath,Body=logstring)
        status="success"
        successmessage=logfilepath+" written Successfully"
        return(status, successmessage, s3_response)
      except Exception as Error:
        status="error"
        errormessage=logfilepath+" written Failed"
        return(status, errormessage, Error)
    else:
      status="error"
      errormessage="Log Writing Error"
      return(status, errormessage, Error)

def func_output(state,status,step,status_message,status_data,path,s3_client,bucket_name):
  outputfile_path=path+"/output.json"
  logfile_path=path+"/log.json"
  output={
    "status": state,
    "Initiated": None,
    "Error": None,
    "Running": None,
    "Degraded": None
  }
  output[state]={
      "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
      "step": step,
      "status": status,
      "status_message": status_message
    }
  if status == "Error":
    output[state]['error_message']=str(status_data)


  status,statusmessage,response=write_output_file(s3_client,bucket_name,outputfile_path,{"state": output})
  if status == "error":
    return(status,statusmessage,response)
  status,statusmessage,response=write_log_file(s3_client,bucket_name,logfile_path, output)
  if status == "error":
    return(status,statusmessage,response)
  statusmessage="Output written to s3"
  return("success", statusmessage,output)