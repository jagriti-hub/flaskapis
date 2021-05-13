from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json

product_api = Blueprint('product_api', __name__)
s3_client=boto3.client("s3")

def uniqid(prefix):
    m = time.time()
    sec = math.floor(m)
    ran = random.randint(0,96764685)
    usec = math.floor(ran * (m - sec))
    a= usec+sec
    x = '%3x' % (a)
    l = list(x)
    random.shuffle(l)
    y = ''.join(l)
    uniqid = prefix+y
    return uniqid

def load_s3_file(bucket_name, filepath):
	try:
		file_object=s3_client.get_object(Bucket=bucket_name,Key=filepath)["Body"].read()
		data=json.loads(file_object)
		successmessage=filepath+" loaded Successfully"
		return("success", successmessage, data)
	except Exception as Error:
		errormessage=filepath+" not found"
		return("error", errormessage, str(Error))
		
def write_s3_file(bucket_name, path, data):
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

@product_api.route('/design/v1/product', methods=['POST'])
def createproduct():
	iop = {
        "userid": "",
        "productname": ""
	}
	state_store=os.getenv("state_store")
	userid = request.headers["userid"]
	productname = request.json["productname"]
	productpath= "products/products.json"

	status,statusmessage,products=load_s3_file(state_store,productpath)
	if status != "success":
		products=[]
	productids = []
	for prod in products:
		productids.append(prod["productid"])
	a = True
	while a is True:
		productid=uniqid('prod')
		if productid in productids:
			a = True
		else:
			a = False
	product={
		'productid':productid,
		'userid':userid,
		'productname':productname
	}
	products.append(product)
	status,statusmessage,response=write_s3_file(state_store,productpath,products)
	if status == "success":
		message={"statusCode": 200,"message":"New Product Created","body":product}
	else:
		message={"statusCode": 400,"errorMessage": statusmessage, "Error": response}
	return(message)

@product_api.route("/design/v1/product", methods=["GET"])
def getproduct():
	iop={
		"userid": ""
	}
	state_store=os.getenv("state_store")
	userid = request.headers["userid"]
	productpath= "products/products.json"
	status,statusmessage,products=load_s3_file(state_store,productpath)
	if status == "success":
		res=[]
		for prod in products:
			if prod["userid"]==userid:
				res.append(prod)
		message={"statusCode": 200,"body":res}
	else:
		message={"errorMessage": statusmessage, "Error": products}
	return(message)

@product_api.route("/design/v1/product/<productid>", methods=["GET"])
def getproductbyid(productid):
	state_store=os.getenv("state_store")
	productpath= "products/products.json"
	status,statusmessage,products=load_s3_file(state_store,productpath)
	if status == "success":
		product={}
		for prod in products:
			if prod["productid"]==productid:
				product=prod
		message={"statusCode": 200,"body":product}
	else:
		message={"errorMessage": statusmessage, "Error": products}
	return(message)

@product_api.route('/design/v1/product/<productid>', methods=['DELETE'])
def deleteproduct(productid):
	state_store=os.getenv("state_store")
	productpath= "products/products.json"
	status,statusmessage,products=load_s3_file(state_store,productpath)
	if status == "success":
		productids = []
		for prod in products:
			productids.append(prod["productid"])
		if productid in productids:
			for prod in products:
				if prod["productid"] == productid:
					products.remove(prod)
			status,statusmessage,response=write_s3_file(state_store,productpath,products)
			message={"statusCode": 200, 'message':'Product Deleted'}
		else:
			message={"statusCode": 400,"errorMessage":"productid does not exist"}
	else:
		message={"errorMessage": statusmessage, "Error": products}
	return(message)