import os,sys,time,logging,json,random,math
import pprint,base64,re,requests
from datetime import datetime
import boto3
from boto3 import session
import docker
import jsonpickle
import kubernetes
from kubernetes import client, config
import s3files

def build_code_generate(code_path,resourceid,methodid,method_path,dbid):
    if os.path.isdir("./"+resourceid) == False:
        os.mkdir("./"+resourceid)
    if os.path.isdir("./"+resourceid+"/code")==False:
        os.mkdir("./"+resourceid+"/code") 
    
    status,status_message,mid_code=s3files.load_code_file(method_path+"/"+methodid+"/code/"+methodid+".py", "./"+resourceid+"/code/"+methodid+".py")
    with open(mid_code, 'r+') as f:
        codefileread = f.read()
    codefile=codefileread.replace("dynamodb=boto3.resource('dynamodb',region_name='us-east-1')","dynamodb = boto3.resource('dynamodb',endpoint_url='http://"+ dbid +"',region_name='us-east-1')")
    print(codefile)
    with open("./"+resourceid+"/code/"+methodid+".py","w") as f:
        f.write(codefile)
    pythonfiles={
        "methodidcodefile": mid_code
    }
    return("success","methodid.py files created",pythonfiles)

def generate_app_python_file(resourceid, blueprint_import,import_blueprint_form):
    print("Generating app.py for Flask")
    appcode_path = "./"+resourceid+"/code"
    import_module = 'from flask import Flask\n'
    import_blueprint = import_blueprint_form
    flask_initialise = "app = Flask(__name__)"
    add_blueprint = blueprint_import
    main_func = 'if __name__ == \"__main__\":\n    app.run()'

    try:
      app_py_path=appcode_path+"/app.py"
      app_py = open(app_py_path, "w")
      app_py.write(import_module + "\n"+"\n".join(import_blueprint)+"\n\n" + flask_initialise + "\n\n" + "\n".join(add_blueprint) + "\n\n" + main_func + "\n\n")
      app_py.close()
      successmessage = app_py_path+" created Successfully"
      return("success",successmessage,app_py_path)
    except Exception as Error:
      return("error","Python_WSGI_Codefile_Write_error",Error)

def generate_docker_file(resourceid):
    print("Generating Dockerfile for deployment")
    try:
        dokerfilepath= "./"+resourceid+"/"+"Dockerfile"
        dockerfilef = open(dokerfilepath, "w")
        dockerfilef.write('FROM python:3.8.1-slim-buster\nRUN addgroup --system app && adduser --system --ingroup app app\nENV APP_HOME=/home/app/web\nRUN mkdir $APP_HOME\nWORKDIR $APP_HOME\nADD code $APP_HOME\nRUN pip install --upgrade pip -r requirement.txt\nRUN chown -R app:app $APP_HOME\nUSER app\nCMD [\"gunicorn\", \"--bind\", \"0.0.0.0:5000\", \"app:app\"]')
        dockerfilef.close()
        successmessage = dokerfilepath+" created Successfully"
        return("success",successmessage,dokerfilepath)
    except Exception as Error:
        return("error","Dockerfile_Write_error",Error)

def generate_requirement_file(resourceid,requirement_data):
    print("Generating requirement for deployment")
    try:
        requirement_filepath= "./"+resourceid+"/code/"+"requirement.txt"
        requirementf = open(requirement_filepath, "w")
        requirementf.write("\n".join(requirement_data))
        requirementf.close()
        successmessage = requirement_filepath+" created Successfully"
        return("success",successmessage,requirement_filepath)
    except Exception as Error:
        return("error","Dockerfile_Write_error",Error)