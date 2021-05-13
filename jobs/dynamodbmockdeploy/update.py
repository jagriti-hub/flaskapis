import logging
import os
import json,time
import sys
import boto3
from boto3 import session
from datetime import datetime
import s3files 
      
def delete_dynamodb_table(Input,Region,dbid):
  try:
    dynamodb = boto3.client("dynamodb",endpoint_url='http://'+dbid,region_name = Region)
    response = dynamodb.delete_table(
        TableName=Input['tablename']
    )
    return("success","Table_successfully_deleted")
  except Exception as e:
    return("failed",str(e))
 
    
def create_dynamodb_table_deployment(Input,Region,dbid):
  try:
    print("table initiated")
    dynamodb = boto3.client("dynamodb",endpoint_url='http://'+dbid,region_name = Region)
    # dynamodb = boto3.client("dynamodb",region_name = Region)
    logging.info("table start creating : " + Input['tablename'])
    primarykeyname = Input["indexes"]["primary"]["key"]
    try:
      sortkeyname = Input["indexes"]["primary"]["sortkey"]
    except:
      sortkeyname = ""
    for attribute in Input["schema"]:
      if attribute["attributename"] == primarykeyname:
        primarykeyatt = attribute["attributetype"]
        primarykeyname = attribute["attributename"]
      elif attribute["attributename"] == sortkeyname:
        sortkeyname = attribute["attributename"]
        sortkeyatt = attribute["attributetype"]
    if Input["indexes"]["primary"]["infra"]["ondemand"] == True:
      if  sortkeyname == "":
        response = dynamodb.create_table(
          AttributeDefinitions=[
            {
              'AttributeName': primarykeyname,
              'AttributeType': primarykeyatt
            }
          ],
          TableName=Input['tablename'],
          KeySchema=[
            {
              'AttributeName': primarykeyname,
              'KeyType': 'HASH'
            }
          ],
          BillingMode = 'PAY_PER_REQUEST'
        )
      elif sortkeyname!= "":
        response = dynamodb.create_table(
          AttributeDefinitions=[
            {
              'AttributeName': primarykeyname,
              'AttributeType': primarykeyatt
            },
            {
              'AttributeName': sortkeyname,
              'AttributeType': sortkeyatt
            }
          ],
          TableName=Input['tablename'],
          KeySchema=[
            {
              'AttributeName': primarykeyname,
              'KeyType': 'HASH'
            },
            {
              'AttributeName': sortkeyname,
              'KeyType': 'RANGE'
            }
          ],
          BillingMode='PAY_PER_REQUEST'
        )
      waiter = dynamodb.get_waiter('table_exists')
      waiter.wait(TableName=Input['tablename'])
    elif Input["indexes"]["primary"]["infra"]["ondemand"] == False:
      if  sortkeyname == "":
        response = dynamodb.create_table(
          AttributeDefinitions=[
            {
              'AttributeName': primarykeyname,
              'AttributeType': primarykeyatt
            }
          ],
          TableName=Input['tablename'],
          KeySchema=[
            {
              'AttributeName': primarykeyname,
              'KeyType': 'HASH'
            }
          ],
          BillingMode='PROVISIONED',
          ProvisionedThroughput={
            'ReadCapacityUnits': Input["indexes"]["primary"]["infra"]["iops"]["read"],
            'WriteCapacityUnits': Input["indexes"]["primary"]["infra"]["iops"]["write"]
          }
        )
      elif sortkeyname!= "":
        response = dynamodb.create_table(
          AttributeDefinitions=[
            {
              'AttributeName': primarykeyname,
              'AttributeType': primarykeyatt
            },
            {
              'AttributeName': sortkeyname,
              'AttributeType': sortkeyatt
            }
          ],
          TableName=Input['tablename'],
          KeySchema=[
            {
              'AttributeName': primarykeyname,
              'KeyType': 'HASH'
            },
            {
              'AttributeName': sortkeyname,
              'KeyType': 'RANGE'
            }
          ],
          BillingMode='PROVISIONED',
          ProvisionedThroughput={
            'ReadCapacityUnits': Input["database"]["dynamodb"]["infra"]["readiops"],
            'WriteCapacityUnits': Input["database"]["dynamodb"]["infra"]["writeiops"]
          }
        )
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=Input['tablename'])
    logging.info("table successfully created : " + Input['tablename'])
    return("success","TABLE_SUCCESSFULLY_CREATED")
  except Exception as e:
    print(e)
    logging.error("table failed to create : " + Input['tablename'])
    return("failed",str(e))


def create_dynamodb_secondary_index(Input,secondarykey,Region,dbid):
  dynamodb = boto3.client("dynamodb",endpoint_url='http://'+ dbid,region_name = Region)
  # dynamodb = boto3.client("dynamodb",region_name = Region)
  indexnames=[]
  try:
    response1 = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
    for index in response1:
      indexnames.append(index['IndexName'])
  except Exception as e:
    print(e)
  try:
    json_output = {}
    secondarykeyname = secondarykey["key"]
    print(secondarykeyname)
    secondarysortkeyname = secondarykey["sortkey"]
    for attribute in Input["schema"]:
      if attribute["attributename"] == secondarykeyname:
        secondarykeyatt = attribute["attributetype"]
        secondarykeyname = attribute["attributename"]
      elif attribute["attributename"] == secondarysortkeyname:
        secondarysortkeyname = attribute["attributename"]
        secondarysortkeyatt = attribute["attributetype"]
    if secondarykeyname != "":
      if secondarykeyname not in indexnames:
        logging.info("secondary key start creating : " + secondarykeyname)
        if Input["indexes"]["primary"]["infra"]["ondemand"] == True:
          if secondarysortkeyname == "":
            response = dynamodb.update_table(
              AttributeDefinitions=[
                {
                  'AttributeName': secondarykeyname,
                  'AttributeType': secondarykeyatt
                }
              ],
              TableName=Input['tablename'],
              GlobalSecondaryIndexUpdates=[
                {
                  'Create': {
                      'IndexName': secondarykey["indexname"],
                      'KeySchema': [
                          {
                            'AttributeName': secondarykeyname,
                            'KeyType': 'HASH'
                          },
                      ],
                      'Projection': {
                        'ProjectionType': 'ALL',
                      }
                  },
                },
              ],
            )
            indexres = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
            count=0
            for state in indexres:
              if state['IndexStatus'] == 'CREATING':
                counter=count
                status = state['IndexStatus']
                while status != 'ACTIVE':
                  print(status)
                  time.sleep(5)
                  response1 = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
                  status = response1[counter]['IndexStatus']
              count = count+1
          elif secondarysortkeyname != "":
            response = dynamodb.update_table(
              AttributeDefinitions=[
                {
                  'AttributeName': secondarykeyname,
                  'AttributeType': secondarykeyatt
                },
                {
                  'AttributeName': secondarysortkeyname,
                  'AttributeType': secondarysortkeyatt
                }
              ],
              TableName=Input['tablename'],
              GlobalSecondaryIndexUpdates=[
                  {
                    'Create': {
                      'IndexName': secondarykey["indexname"],
                      'KeySchema': [
                        {
                          'AttributeName': secondarykeyname,
                          'KeyType': 'HASH'
                        },
                        {
                          'AttributeName': secondarysortkeyname,
                          'KeyType': 'RANGE'
                        }
                      ],
                      'Projection': {
                        'ProjectionType': 'ALL',
                      }
                    },
                  },
              ],
            )
            indexres = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
            count=0
            for state in indexres:
              if state['IndexStatus'] == 'CREATING':
                counter=count
                status = state['IndexStatus']
                while status != 'ACTIVE':
                  print(status)
                  time.sleep(5)
                  response1 = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
                  status = response1[counter]['IndexStatus']
              count = count+1
        elif Input["indexes"]["primary"]["infra"]["ondemand"] == False:
          if secondarysortkeyname == "":
            response = dynamodb.update_table(
              AttributeDefinitions=[
                  {
                      'AttributeName': secondarykeyname,
                      'AttributeType': secondarykeyatt
                  }
              ],
              TableName=Input['tablename'],
              GlobalSecondaryIndexUpdates=[
                  {
                    'Create': {
                      'IndexName': secondarykey["indexname"],
                      'KeySchema': [
                          {
                            'AttributeName': secondarykeyname,
                            'KeyType': 'HASH'
                          },
                      ],
                      'Projection': {
                        'ProjectionType': 'ALL',
                      },
                      'ProvisionedThroughput': {
                        'ReadCapacityUnits': secondarykey["readiops"],
                        'WriteCapacityUnits': secondarykey["infra"]["writeiops"]
                      }
                    },
                  },
              ],
            )
            indexres = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
            count=0
            for state in indexres:
              if state['IndexStatus'] == 'CREATING':
                counter=count
                status = state['IndexStatus']
                while status != 'ACTIVE':
                  print(status)
                  time.sleep(5)
                  response1 = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
                  status = response1[counter]['IndexStatus']
              count = count+1
          elif secondarysortkeyname != "":
            response = dynamodb.update_table(
              AttributeDefinitions=[
                  {
                      'AttributeName': secondarykeyname,
                      'AttributeType': secondarykeyatt
                  },
                  {
                      'AttributeName': secondarysortkeyname,
                      'AttributeType': secondarysortkeyatt
                  }
              ],
              TableName=Input['tablename'],
              GlobalSecondaryIndexUpdates=[
                {
                  'Create': {
                    'IndexName': secondarykey["indexname"],
                    'KeySchema': [
                      {
                        'AttributeName': secondarykeyname,
                        'KeyType': 'HASH'
                      },
                      {
                        'AttributeName': secondarysortkeyname,
                        'KeyType': 'RANGE'
                      }
                    ],
                    'Projection': {
                      'ProjectionType': 'ALL',
                    },
                    'ProvisionedThroughput': {
                      'ReadCapacityUnits': secondarykey["infra"]["readiops"],
                      'WriteCapacityUnits': secondarykey["infra"]["writeiops"]
                    }
                  },
                },
              ],
            )
            indexres = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
            count=0
            for state in indexres:
                if state['IndexStatus'] == 'CREATING':
                    counter=count
                    status = state['IndexStatus']
                    while status != 'ACTIVE':
                        print(status)
                        time.sleep(5)
                        response1 = dynamodb.describe_table(TableName=Input['tablename'])['Table']['GlobalSecondaryIndexes']
                        status = response1[counter]['IndexStatus']
                count = count+1
      else:
          print('no secondarykey attribute present for create')
    return("success","SECONDARY_KEY_SUCCESSFULLY_CREATED")
  except Exception as e:
    return("failed",str(e))    
    

def main():
  table_path = sys.argv[1]
  dbid = sys.argv[2]
  tableid = sys.argv[3]
  Region = sys.argv[4]
  table_configfile=table_path+"/config.json"
  table_outputfile=table_path+"/output.json"
  table_logfile=table_path+"/log.json"
  status,status_message,tableconfig=s3files.load_config_file(table_configfile)
  if status == "error":
    return(status,status_message,tableconfig)
  output={
    "status": "Initiated",
    "Initiated": {
      "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
      "step": "table_configfile_loading",
      "status": status,
      "status_message": status_message
    },
    "Error": None,
    "Running": None,
    "Degraded": None
  }
  table_output={"state": output}

  status,statusmessage,response=s3files.write_output_file(table_outputfile, output)
  if status == "error":
    return(status,statusmessage,response)
  status,statusmessage,response=write_log_file(bucket_name, table_logfile, output)
  if status == "error":
    return(status,statusmessage,response)
  tablename = tableconfig["tablename"]
  table_status,table_status_message = delete_dynamodb_table(tableconfig,Region,dbid)
  if table_status == "success":
    output={
      "status": "Initiated",
      "Initiated": None,
      "Running": None,
      "Error": {
        tablename: {
          "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
          "step": "1_DELETE_TABLE " + tablename,
          "status": table_status,
          "status_message": table_status_message,
        }
      },
      "Degraded": None
    }
  elif table_status == "failed":
    output={
      "status": "Error",
      "Initiated": None,
      "Running": None,
      "Error": {
        tablename: {
          "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
          "step": "1_DELETE_TABLE " + tablename,
          "status": table_status,
          "status_message": table_status_message,
        }
      },
      "Degraded": None
    }
  table_output_state={"state": output}
  tableconfig.update(table_output_state)
  status,statusmessage,response=s3files.write_output_file(table_outputfile, tableconfig)
  if status == "error":
    return(status,statusmessage,response)
  status,statusmessage,response=s3files.write_log_file(table_logfile, output)
  if status == "error":
    return(status,statusmessage,response)
  
  table_status,table_status_message = create_dynamodb_table_deployment(tableconfig,Region,dbid)
  print(table_status_message)
  if table_status == "success":
    table_output_status = {
      tablename: {
        "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
        "step": "1_CREATE_TABLE " + tablename,
        "status": table_status,
        "status_message": table_status_message,
      }
    }
  elif table_status == "failed":
    output={
      "status": "Error",
      "Initiated": None,
      "Running": None,
      "Error": {
        tablename: {
          "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
          "step": "1_CREATE_TABLE " + tablename,
          "status": table_status,
          "status_message": table_status_message,
        }
      },
      "Degraded": None
    }
    table_output_state={"state": output}
    tableconfig.update(table_output_state)
    status,statusmessage,response=s3files.write_output_file(table_outputfile, tableconfig)
    if status == "error":
      return(status,statusmessage,response)
    status,statusmessage,response=s3files.write_log_file(table_logfile, output)
    if status == "error":
      return(status,statusmessage,response)
  
  secondary_key_output = {}
  secondary_key_output.update(table_output_status)
  secondary_status_check = "success"
  if table_status == "success":
    for secondarykey in tableconfig["indexes"]["secondary"]:
      secondarykeyname = secondarykey["key"]
      secondary_status,secondarykey_status_message = create_dynamodb_secondary_index(tableconfig,secondarykey,Region,dbid)
      outputstatus={
        secondarykeyname: {
          "timestamp": datetime.now().strftime('%d-%m-%Y_%H:%M:%s'),
          "step": "2_CREATE_SECONDARY_KEY " + secondarykeyname,
          "status": secondary_status,
          "status_message": secondarykey_status_message,
        }
      }
      if secondary_status == "failed":
        secondary_status_check = "failed"
      secondary_key_output.update(outputstatus)
    if secondary_status_check == "success":
      output={
        "status": "Running",
        "Initiated": None,
        "Error": None,
        "Running": secondary_key_output,
        "Degraded": None
      }
    elif secondary_status_check == "failed":
      output={
        "status": "Degraded",
        "Initiated": None,
        "Error": None,
        "Degraded": secondary_key_output,
        "Running": None
      }
    table_output_state={"state": output}
    tableconfig.update(table_output_state)
    status,statusmessage,response=s3files.write_output_file(table_outputfile, tableconfig)
    if status == "error":
      return(status,statusmessage,response)
    status,statusmessage,response=s3files.write_log_file(bucket_name, table_logfile, output)
    if status == "error":
      return(status,statusmessage,response)
  return("success",statusmessage,response)
  
FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.ERROR)
status,statusmessage,response=main()
if status == "error":
  logging.error(statusmessage+"-"+str(response))
if status == "success":
  logging.info(statusmessage+"-"+str(response))
    
  