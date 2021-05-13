import json,os,sys,shutil
from shutil import copyfile
datapath=os.getenv("archedatapath")

def load_s3_file(filepath):
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
		
def write_s3_file(path, data):
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

def write_txt_file(path, data):
	try:
		datawritepath=datapath+"/"+path
		directory = os.path.dirname(datawritepath)
		if not os.path.exists(directory):
			os.makedirs(directory)
		data_folder=open(datawritepath,"w+")
		data_folder.write(data)
		status="success"
		successmessage=path+" written Successfully"
		return(status, successmessage, path)
	except Exception as Error:
		status="error"
		errormessage=path+" written Failed"
		return(status, errormessage, str(Error))

def delete_s3_file(path):
	deletepath=datapath+"/"+path
	if os.path.exists(deletepath):
		os.remove(deletepath)
		successmessage=path+" deleted Successfully"
		return("success",successmessage,path)
	else:
		errormessage=path+" deletion Failed"
		Error="file does not exist"
		return("error", errormessage, str(Error))

def delete_folders(prefix):
	delete_prefix=datapath+"/"+prefix
	try:
		shutil.rmtree(delete_prefix)
		message="folder deleted"
		return("success",message)
	except OSError as e:
		return("error",str(e))

def load_code_file(sourcepath,destinationpath):
	try:
		srcpath=datapath+"/"+sourcepath
		destpath=datapath+"/"+destinationpath
		directory = os.path.dirname(destpath)
		if not os.path.exists(directory):
			os.makedirs(directory)
		copyfile(srcpath, destpath)
		successmessage=destinationpath+" created Successfully"
		return('success',successmessage,destinationpath)
	except OSError as e:
		errormessage=destinationpath+"CREATION_FAILED"
		return("error",errormessage,str(e))

def load_txt_file(filepath):
	path=datapath+"/"+filepath
	if os.path.exists(path):
		file_object=open(path,"r")
		datastring=file_object.read()
		successmessage=filepath+" loaded Successfully"
		return("success", successmessage, datastring)
	else:
		errormessage=filepath+" not found"
		Error="file does not exist"
		return("error", errormessage, str(Error))