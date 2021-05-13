import boto3,json,os,sys,time
s3_client = boto3.client('s3')
def list_object_byprefix(bucket_name, prefix):
    try:
        list_object = s3_client.list_objects(
            Bucket=bucket_name,
            Prefix=prefix
        )
        object_contents = list_object["Contents"]
        object_keys = []
        for objects in object_contents:
            object_keys.append(objects["Key"])
        return(object_keys)
    except Exception as e:
        return(str(e))
objectkeys = list_object_byprefix("mockjsdeploytest","t12345/s12345/api/v1/resources/r123457")
print(objectkeys)

# def load_s3_file(bucket_name, filepath):
# 	try:
# 		file_object=s3_client.get_object(Bucket=bucket_name,Key=filepath)["Body"].read()
# 		data=json.loads(file_object)
# 		successmessage=filepath+" loaded Successfully"
# 		return("success", successmessage, data)
# 	except Exception as Error:
# 		errormessage=filepath+" not found"
# 		return("error", errormessage, str(Error))

# services = []
# for obj in objectkeys:
#     status,statusmessage,service=load_s3_file("mockjsdeploytest", obj)
#     services.append(service)
#     # print(type(obj))
# print(services)

def delete_s3_file(bucket_name,path):
	try:
		s3_response=response = s3_client.delete_object(Bucket=bucket_name,Key=path)
		status="success"
		successmessage=path+" deleted Successfully"
		return(status, successmessage, s3_response)
	except Exception as Error:
		status="error"
		errormessage=path+" deletion Failed"
		return(status, errormessage, str(Error))

# status,statusmessage,response = delete_s3_file("mockjsdeploytest","t12345/s12345/api/v1/resources/r123457/abc.json")
# print(status,statusmessage,response)