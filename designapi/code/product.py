from flask import Flask, jsonify
from flask import Blueprint
from flask import request
import sys,os,boto3,time,math,random
import logging,json
import datafile

logger=logging.getLogger()
product_api = Blueprint('product_api', __name__)

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

@product_api.route('/design/v1/product', methods=['POST'])
def createproduct():
	iop = {
        "userid": "",
        "productname": ""
	}
	userid = request.headers["userid"]
	productname = request.json["productname"]
	json_dict = request.get_json()
	productpath= "products/products.json"
	status,statusmessage,products=datafile.load_s3_file(productpath)
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
	if "description" in json_dict:
		product["description"]=request.json["description"]
	products.append(product)
	status,statusmessage,response=datafile.write_s3_file(productpath,products)
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
	userid = request.headers["userid"]
	productpath= "products/products.json"
	status,statusmessage,products=datafile.load_s3_file(productpath)
	if status != "success":
		res=[]
	elif status == "success":
		res=[]
		for prod in products:
			if prod["userid"]==userid:
				res.append(prod)
	message={"statusCode": 200,"body":res}
	return(message)

@product_api.route("/design/v1/product/<productid>", methods=["GET"])
def getproductbyid(productid):
	productpath= "products/products.json"
	status,statusmessage,products=datafile.load_s3_file(productpath)
	if status == "success":
		productids = []
		for prod in products:
			productids.append(prod["productid"])
		if productid in productids:
			product={}
			for prod in products:
				if prod["productid"]==productid:
					product=prod
			message={"statusCode": 200,"body":product}
		else:
			message={"statusCode": 400,"errorMessage":"productid does not exist"}
	else:
		message={"statusCode": 400, "errorMessage": products}
	return(message)

@product_api.route('/design/v1/product/<productid>', methods=['DELETE'])
def deleteproduct(productid):
	productpath= "products/products.json"
	status,statusmessage,products=datafile.load_s3_file(productpath)
	if status == "success":
		productids = []
		for prod in products:
			productids.append(prod["productid"])
		if productid in productids:
			for prod in products:
				if prod["productid"] == productid:
					products.remove(prod)
			status,statusmessage,response=datafile.write_s3_file(productpath,products)
			prodprefix="services/"+productid
			delstatus,delmessage=datafile.delete_folders(prodprefix)
			message={"statusCode": 200, 'message':'Product Deleted'}
		else:
			message={"statusCode": 400,"errorMessage":"productid does not exist"}
	else:
		message={"statusCode": 400, "errorMessage": products}
	return(message)