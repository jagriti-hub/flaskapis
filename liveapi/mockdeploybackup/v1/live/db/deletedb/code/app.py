from flask import Flask, jsonify
from flask import request
import sys,os,boto3
import logging,json
app = Flask(__name__)
@app.route('/v1/live/db/{dbid}', methods=['DELETE'])
def deletedb():
	successmessage={"status": 200}
	return(successmessage)