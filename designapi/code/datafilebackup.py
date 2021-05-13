import boto3,json,os,sys


s3_client=boto3.client("s3")
bucket_name=os.getenv("state_store")

def load_s3_file(filepath):
	try:
		file_object=s3_client.get_object(Bucket=bucket_name,Key=filepath)["Body"].read()
		data=json.loads(file_object)
		successmessage=filepath+" loaded Successfully"
		return("success", successmessage, data)
	except Exception as Error:
		errormessage=filepath+" not found"
		return("error", errormessage, str(Error))
		
def write_s3_file(path, data):
	try:
		datastring=json.dumps(data)
		s3_response=s3_client.put_object(Bucket=bucket_name,Key=path,Body=datastring)
		status="success"
		successmessage=path+" written Successfully"
		return(status, successmessage, s3_response)
	except Exception as Error:
		status="error"
		errormessage=path+" written Failed"
		return(status, errormessage, str(Error))

def write_txt_file(path, data):
	try:
		s3_response=s3_client.put_object(Bucket=bucket_name,Key=path,Body=data)
		status="success"
		successmessage=path+" written Successfully"
		return(status, successmessage, s3_response)
	except Exception as Error:
		status="error"
		errormessage=path+" written Failed"
		return(status, errormessage, str(Error))

def delete_s3_file(path):
	try:
		s3_response=response = s3_client.delete_object(Bucket=bucket_name,Key=path)
		status="success"
		successmessage=path+" deleted Successfully"
		return(status, successmessage, s3_response)
	except Exception as Error:
		status="error"
		errormessage=path+" deletion Failed"
		return(status, errormessage, str(Error))

def list_object_byprefix(prefix):
    try:
        list_object = s3_client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix
        )
        object_contents = list_object["Contents"]
        object_keys = []
        for objects in object_contents:
            object_keys.append(objects["Key"])
        return("success",object_keys)
    except Exception as e:
        return("error",str(e))

def delete_folders(prefix):
	try:
		status,objectkeys=list_object_byprefix(prefix)
		if status == "success":
			overalldelstatus=[]
			for objectkey in objectkeys:
				delstatus,delstatusmessage,delete=delete_s3_file(objectkey)
				overalldelstatus.append(delstatus)
			if "error" in overalldelstatus:
				return("error","delete_folder_failed")
			else:
				return("success","folder_deleted")
		else:
			return(status,obejctkeys)
	except Exception as e:
		return("error",str(e))