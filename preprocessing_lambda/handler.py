import preprocessor
import json
import urllib.parse
import boto3
from io import BytesIO

def handler(event, context):
    
    
    bedrock = boto3.client(service_name='bedrock-runtime',
                                    region_name='us-east-1', )
    client = boto3.client('s3')
    sqs_client = boto3.client('sqs')
    
    preprop = preprocessor.Preprocessor(bedrock)
    IMG_QUEUE = "https://sqs.us-east-1.amazonaws.com/779846784630/ia-architecture-deployment-ImgQueueE4D1F2D6-vwiQD4xSbkJo"
    TABLE_QUEUE = "https://sqs.us-east-1.amazonaws.com/779846784630/ia-architecture-deployment-TbQueueAC2B3CF4-JHQTneJSIjlD"
    TEXT_QUEUE = "https://sqs.us-east-1.amazonaws.com/779846784630/ia-architecture-deployment-TxtQueue0962BFE5-KkH0bfy1I6Zj"
    
    print("NEW HANDLER INVOCATION")
    
    try: 
        bucket_name = "sgd-rag-test"
        folder_name = "Documentos/"
        
        # List objects in the specified folder
        #response = client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        
        
        if key.endswith('.pdf'):
            
            pdf_object = client.get_object(Bucket=bucket_name, Key=key)
            pdf_content = pdf_object['Body'].read()
            
            try: 
                
                pdf_reader, label = preprop.read_document(key, BytesIO(pdf_content), "Images/")

                #if label == "Anexo":
                #    return {
                #        "status": "error",
                #        "body": json.dumps("Ommited Anexo")}
                # enqueue to a sqs information to a sqs queue
                for page in pdf_reader:
                    page['document_name'] = key
                    page['document_label'] = label
                    
                    message_body = json.dumps(page)
                    print(f"Message body: {message_body}", label)
                    """response = sqs_client.send_message(QueueUrl=IMG_QUEUE, MessageBody=message_body)                   
                    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                        raise Exception("Error enqueuing message to sqs")"""
                    
                    response = sqs_client.send_message(QueueUrl=TEXT_QUEUE, MessageBody=message_body)   
                    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                        raise Exception("Error enqueuing message to sqs")  
                    
                    """response = sqs_client.send_message(QueueUrl=TABLE_QUEUE, MessageBody=message_body)     
                    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                        raise Exception("Error enqueuing message to sqs")"""
            except Exception as e:
                raise Exception(f"Error processing the document : {str(e)}")
            
                        
                        
                        
                        
                        
                        
                        
        
        return {
            "status": "success",
            "body": json.dumps("All objects processed successfully")            
        }
        
    except Exception as e: 
        return {
            "status": "error",
            "body": json.dumps(str(e))
        }
