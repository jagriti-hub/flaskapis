import json,os,sys
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