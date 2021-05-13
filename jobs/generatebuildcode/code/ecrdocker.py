import os,sys,time,logging,json,random,math
import pprint,base64,re
from datetime import datetime
import boto3
from boto3 import session
import docker
import jsonpickle
import kubernetes
from kubernetes import client, config


def create_ecr_repo(connection,region,ecr_repo_name):
  try:
    ecr_client = connection.client('ecr', region_name = region)
    create_repo_out = ecr_client.create_repository( repositoryName=ecr_repo_name )
    ecr_registryId = create_repo_out['repository']['registryId']
    RepoStatus = "ECR_REPO_CREATE_SUCCESS"
    ecrrepo={
      "ecr_repo_name": ecr_repo_name,
      "ecr_registryId": ecr_registryId
      }
    return("success",RepoStatus,ecrrepo)
  except Exception as Error:
    if "RepositoryAlreadyExistsException" in str(Error):
      describe_repo_out = ecr_client.describe_repositories( repositoryNames= [ecr_repo_name] )
      ecr_repo_name = describe_repo_out['repositories'][0]['repositoryName']
      ecr_registryId = describe_repo_out['repositories'][0]['registryId']
      RepoStatus = "ECR_REPO_EXIST"
      ecrrepo={
        "ecr_repo_name": ecr_repo_name,
        "ecr_registryId": ecr_registryId
      }
      return("success",RepoStatus,ecrrepo)
    else:
      RepoStatus = "ECR_REPO_CREATE_ERROR"
      RepoErrorDescription = Error
      response={
      "RepoErrorDescription": RepoErrorDescription
      }
      return("error",RepoStatus,response)


def ecr_docker_login(connection,region):
  try:
    ecr_client = connection.client('ecr', region_name = region)
    token = ecr_client.get_authorization_token()
  except Exception as Error:
    return("error","ECR_REPO_LOGIN_ERROR",str(Error))
  username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
  auth_config = {'username': username, 'password': password}
  return("success","ECR_REPO_LOGIN_SUCCESS",auth_config)


def docker_push(imagetag):
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
  except Exception as Error:
    return("error","DOCKER_BUILD_MACHINE_CONNECT_ERROR",Error)
  pushlog = list((client.images.push(repository=imagetag, stream=True, decode=True)))
  if pushlog[-3]['status'] == 'Pushed' or pushlog[-3]['status'] == 'Layer already exists':
    response={
      "PushLog": pushlog
    }
    print("DOCKER_PUSH_SUCCESS")
    return("success","DOCKER_PUSH_SUCCESS",response)
    
  else:
    imagestatus = "DOCKER_PUSH_FAILED"
    response = {
      "PushLog": pushlog,
      "Pushstatus": pushlog[-3]['status']
    }
    return("error","Docker_push_Failed",response)


def docker_build(imagename,buildtag,dockerhost,build_path):
  buildlog=[]
  imagetag=dockerhost+imagename+":"+buildtag
  print("starting response")
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
  except Exception as Error:
    return("error","DOCKER_BUILD_MACHINE_CONNECT_ERROR",Error)
  response = [line for line in client.api.build(decode='true',tag=imagetag,path=build_path)]
  imageid = None
  for item in response:
    if "stream" in item.keys():
      buildlog.append(item['stream'])
    if "aux" in item.keys():
      imageid = item['aux']['ID']
    if "errorDetail" in item.keys():  
      builderrordetails = item['errorDetail']
    if "error" in item.keys():
      builderror = item['error']
  if imageid is not None:
    print("imageid from ecrdocker file: ",imageid)
    response={
      "imagetag": imagetag,
      "buildlog": buildlog
    }
    return("success","DOCKER_BUILD_SUCCESS",response)
  else:
    response={
      "imagetag": imagetag,
      "buildlog": buildlog,
      "errormessage": builderror,
      "errordetail": builderror
    }
    return("error","DOCKER_BUILD_ERROR",response)