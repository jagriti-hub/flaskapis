import json,os,sys
from shutil import copyfile
import time
from datetime import datetime
datapath=os.getenv("archeplaydatapath")

def load_config_file(filepath):
	path=datapath+"/"+filepath
	if os.path.exists(path):
		file_object=open(path,"r")
		datastring=file_object.read()
		data=json.loads(datastring)
		successmessage=filepath+" loaded Successfully"
		return("success", successmessage, data)
	else:
		errormessage=filepath+" not found"
		Error="file does not exist"
		return("error", errormessage, str(Error))
		
def write_output_file(path, data):
  try:
    datawritepath=datapath+"/"+path
    directory = os.path.dirname(datawritepath)
    if not os.path.exists(directory):
      os.makedirs(directory)
    datastring=json.dumps(data)
    data_folder=open(datawritepath, "w")
    data_folder.write(datastring)
    os.chown(datawritepath,150,150)
    successmessage=path+" written Successfully"
    return("success", successmessage, path)
  except Exception as Error:
    errormessage=path+" written Failed"
    return("error", errormessage, str(Error))
    
def write_log_file(logfilepath, log):
  try:
    status,status_message,log_file_object=load_config_file(logfilepath)
    if status == "success":
      logfile=log_file_object
      print(logfile)
      logfile["logs"].append(log)
    else:
      logfile={
        "logs": []
      }
      logfile["logs"].append(log)
    writestatus,writestatusmessage,response=write_output_file(logfilepath,logfile)
    if writestatus == "success":
      successmessage=logfilepath+" written Successfully"
      return("success", successmessage, logfile)
    else:
      errormessage=logfilepath+" write failed"
      return("error",errormessage,logfile)
  except Exception as Error:
    errormessage="Log Writing Error"
    return("error", errormessage, Error)


def load_requirement_file(requirementfilepath):
  path=datapath+"/"+requirementfilepath
  if os.path.exists(path):
    file_object=open(path,"r")
    datastring=file_object.read()
    successmessage=requirementfilepath+" loaded Successfully"
    return("success", successmessage, datastring)
  else:
    errormessage=requirementfilepath+" not found"
    Error="file does not exist"
    return("error", errormessage, str(Error))

def func_output(state,status,step,status_message,status_data,path):
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
  if status == "error":
    output[state]['error_message']=str(status_data)

  status,statusmessage,response=write_output_file(outputfile_path,{"state": output})
  if status == "error":
    return(status,statusmessage,response)
  status,statusmessage,response=write_log_file(logfile_path, output)
  if status == "error":
    return(status,statusmessage,response)
  statusmessage="Output written to s3"
  return("success", statusmessage,output)

def load_code_file(sourcepath,destinationpath):
	try:
		srcpath=datapath+"/"+sourcepath
		directory = os.path.dirname(destinationpath)
		if not os.path.exists(directory):
			os.makedirs(directory)
		copyfile(srcpath, destinationpath)
		successmessage=destinationpath+" created Successfully"
		return('success',successmessage,destinationpath)
	except OSError as e:
		errormessage=destinationpath+"CREATION_FAILED"
		return("error",errormessage,str(e))
