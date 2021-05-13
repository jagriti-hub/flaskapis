import sys
import os
import yaml
designfile=sys.argv[1]
designf = open(designfile, "r")
design=yaml.load(designf, Loader=yaml.FullLoader)
for service in design['service']:
  servicepath=service["servicename"]
  if not os.path.exists(servicepath):
      os.makedirs(servicepath)
  for version in service["versions"]:
    versionpath=servicepath+"/"+version["versionid"]
    if not os.path.exists(versionpath):
        os.makedirs(versionpath)
    for resources in version["resources"]:
      resourcepath=versionpath+"/"+resources["resourceid"]
      if not os.path.exists(resourcepath):
        os.makedirs(resourcepath)
      dockercompose={
        "version": "3.7",
        "services": {}
      }
      apigwpath=resourcepath+"/apigw"
      if not os.path.exists(apigwpath):
        os.makedirs(apigwpath)
        
      nginxconf=apigwpath+"/nginx.conf"
      if not os.path.isfile(nginxconf):
        nginxconff = open(nginxconf, "w")
        nginxconff.write('include /etc/nginx/api_gateway.conf;')
        nginxconff.close()
      apigwconf=apigwpath+"/api_gateway.conf"
      if not os.path.isfile(apigwconf):
        apigwconff = open(apigwconf, "w")
        apigwconff.write('events {\n\tworker_connections  4096;\n\t}\nhttp {\n\tinclude api_backends.conf;\n\tlog_format   main \'$remote_addr - $remote_user [$time_local]  $status \'\n\t\'"$request" $body_bytes_sent "$http_referer" \'\n\t\'"$http_user_agent" "$http_x_forwarded_for"\';\n\tserver {\n\t\tset $api_name -;\n\t\tlisten 80;\n\t\tserver_name localhost;\n\t\tinclude api_conf.d/*.conf;\n\t\terror_page 404 = @400;\n\t\tproxy_intercept_errors on;\n\t\tinclude api_json_errors.conf;\n\t\tdefault_type application/json;\n\t}\n}')
        apigwconff.close()
      apibackendconf=apigwpath+"/api_backends.conf"
      if not os.path.isfile(apibackendconf):
        apibackendconff = open(apibackendconf, "w")
        apibackendconff.write('include api_backends_conf.d/*.conf;')
        apibackendconff.close()
      apijsonerrorsconf=apigwpath+"/api_json_errors.conf"
      if not os.path.isfile(apijsonerrorsconf):
        apijsonerrorsconff = open(apijsonerrorsconf, "w")
        apijsonerrorsconff.write('error_page 400 = @400;\nlocation @400 { return 400 \'{"status":400,"message":"Bad request"}\\n\'; }\nerror_page 401 = @401;\nlocation @401 { return 401 \'{"status":401,"message":"Unauthorized"}\\n\'; }\nerror_page 403 = @403;\nlocation @403 { return 403 \'{"status":403,"message":"Forbidden"}\\n\'; }\nerror_page 404 = @404;\nlocation @404 { return 404 \'{"status":404,"message":"Resource not found"}\\n\'; }')
        apijsonerrorsconff.close()
      apibackendpath=apigwpath+"/api_backends_conf.d"
      if not os.path.exists(apibackendpath): 
         os.makedirs(apibackendpath)
      
      apigwdockerfile=apigwpath+"/Dockerfile"
      if not os.path.isfile(apigwdockerfile):
        apigwdockerfilef = open(apigwdockerfile, "w")
        apigwdockerfilef.write('FROM nginx\nCOPY ./nginx.conf /etc/nginx/nginx.conf\nADD ./api_conf.d /etc/nginx/api_conf.d/\nADD ./api_backends_conf.d /etc/nginx/api_backends_conf.d/\nADD ./api_gateway.conf /etc/nginx/\nADD ./api_backends.conf /etc/nginx/\nADD ./api_json_errors.conf /etc/nginx/\nEXPOSE 80')
        apigwdockerfilef.close()
      apiconfpath=apigwpath+"/api_conf.d"
      apicompose={
        "apigw":{
          "build": {
            "context": "./apigw"
          },
          "ports":[
              '80:80'
            ]
        } 
      }
      dockercompose["services"].update(apicompose)
      
      
      if not os.path.exists(apiconfpath): 
         os.makedirs(apiconfpath)
      for method in resources["methods"]:
        methodpath=resourcepath+"/"+method["methodname"]
        if not os.path.exists(methodpath):
            os.makedirs(methodpath)
        codepath=methodpath+"/code"
        if not os.path.exists(codepath):
            os.makedirs(codepath)
        if method["functiontype"] == "python":
          if method["python"]["deploymenttype"] == "flask":
            requirementf = open(codepath + "/requirement.txt", "w")
            for requirement in method["python"]["requirements"]:
              requirementf.write("%s\n" % requirement)
            requirementf.close()
            wsgif = open(codepath + "/wsgi.py", "w")
            wsgif.write('from app import app\nif __name__ == "__main__":\n\tapp.run()\n')
            wsgif.close()
            
            if method["methodpath"] == "NONE":
              methodurlpath="'/"+version["versionid"]+"/"+resources["resourceid"]+"'"
            else:
              methodurlpath="'/"+version["versionid"]+"/"+resources["resourceid"]+"/"+method["methodpath"]+"'"
            appfile=codepath + "/app.py"
            if not os.path.isfile(appfile):
              appf = open(appfile, "w")
              appf.write('from flask import Flask, jsonify\nfrom flask import request\nimport sys,os,boto3\nimport logging,json\napp = Flask(__name__)\n@app.route('+methodurlpath+', methods=[\''+method["methodtype"]+'\'])\ndef '+method["methodname"]+'():\n\tsuccessmessage={"status": 200}\n\treturn(successmessage)')
              appf.close()
            dockerfile=methodpath + "/Dockerfile"
            if not os.path.isfile(dockerfile):
              dockerfilef = open(dockerfile, "w")
              dockerfilef.write('FROM python:3.8.1-slim-buster\nRUN addgroup --system app && adduser --system --ingroup app app\nENV HOME=/home/app\nENV APP_HOME=/home/app/web\nRUN mkdir $APP_HOME\nWORKDIR $APP_HOME\nRUN apt-get update && apt-get install -y --no-install-recommends netcat\nCOPY code/requirement.txt  $APP_HOME/requirement.txt\nRUN pip install --upgrade pip -r requirement.txt\nCOPY code/app.py $APP_HOME\nCOPY code/wsgi.py $APP_HOME\nRUN chown -R app:app $APP_HOME\nUSER app\nCMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]')
              dockerfilef.close()
              
            methodbackendconf=apibackendpath + "/" + method["methodname"] + ".conf"
            methodbackendconff = open(methodbackendconf, "w")
            methodbackendconff.write('upstream '+method["methodname"]+' {\n\tzone inventory_service 64k;\nserver '+method["methodname"]+':5000;\n}')
            methodbackendconff.close()
            
            methodconf=apiconfpath + "/" + method["methodname"] + ".conf"
            methodconff = open(methodconf, "w")
            methodconff.write('location '+methodurlpath+' {\n\tset $upstream '+method["methodname"]+';\n\trewrite ^ /_'+method["methodname"]+' last;\n}'+'\nlocation = /_'+method["methodname"]+' {\n\tinternal;\n\tset $api_name "'+method["methodname"]+'";\n\tproxy_pass http://$upstream$request_uri;\n}')
            methodconff.close()
            if method["environment"] != "NONE":
              methodcompose={
                method["methodname"]:{
                  "build":{
                    "context": "./"+methodpath
                  },
                  "image": method["methodname"],
                  "environment": method["environment"]
                }
              }
            else:
              methodcompose={
                method["methodname"]:{
                  "build":{
                    "context": "./"+method["methodname"]
                  },
                  "image": method["methodname"]
                }
              }
            dockercompose["services"].update(methodcompose)
      dockercomposefilef = open(resourcepath+"/docker-compose.yaml", "w")    
      yaml.dump(dockercompose,dockercomposefilef)
      dockercomposefilef.close()