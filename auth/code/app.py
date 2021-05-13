import json
import time
import urllib.request
from jose import jwk, jwt
from jose.utils import base64url_decode
from flask import Flask, jsonify
from flask import request
import sys,os,boto3
import logging,json
import base64
import random,string
import hashlib,uuid,datetime
def cognitoauth(event,keys,app_client_id):
  token = event['token']
  # get the kid from the headers prior to verification
  headers = jwt.get_unverified_headers(token)
  kid = headers['kid']
  # search for the kid in the downloaded public keys
  key_index = -1
  for i in range(len(keys)):
      if kid == keys[i]['kid']:
          key_index = i
          break
  if key_index == -1:
      print('Public key not found in jwks.json')
      return False
  # construct the public key
  public_key = jwk.construct(keys[key_index])
  # get the last two sections of the token,
  # message and signature (encoded in base64)
  message, encoded_signature = str(token).rsplit('.', 1)
  # decode the signature
  decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
  print(decoded_signature)
  # verify the signature
  if not public_key.verify(message.encode("utf8"), decoded_signature):
    print('Signature verification failed')
    return False
  print('Signature successfully verified')
  # since we passed the verification, we can now safely
  # use the unverified claims
  claims = jwt.get_unverified_claims(token)
  # additionally we can verify the token expiration
  if time.time() > claims['exp']:
      print('Token is expired')
      return False
  # and the Audience  (use claims['client_id'] if verifying an access token)
  if claims['aud'] != app_client_id:
      print('Token was not issued for this audience')
      return False
  # now we can use the claims
  print(claims)
  return claims
app = Flask(__name__)
@app.route('/auth', methods=['POST'])
def create_task():
  token = request.headers["auth"]
  region = 'us-east-1'
  # userpool_id = 'us-east-1_M0O8FmGHe' #production's
  userpool_id = 'us-east-1_kMH6aoDCq'
  # app_client_id = '5ga1kkiuvl9gi77eenoqj1dg6d'  #production's
  app_client_id = '4ocs19eg5o32mf3oo6b7i7t9kt'
  # app_client
  keys_url = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpool_id)
  # instead of re-downloading the public keys every time
  # we download them only on cold start
  # https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/
  with urllib.request.urlopen(keys_url) as f:
    response = f.read()
  keys = json.loads(response.decode('utf-8'))['keys']
  print(keys)
  event = {'token': token}
  claims=cognitoauth(event,keys,app_client_id)
  print(claims)
  if not claims:
    response={
      "status": 400
    }
    return(response,403)
  else:
    response={
      "status": 200
    }
    return(response,201)