import ai_calls
import prompt
import boto3
import base64
import json


def chunking( text : str, chunk_size : int = 1000, overlap : int = 100):
        
    text = text.replace('\n', ' ').split(' ')
    text = " ".join(text)
        
    
    chunks = [  text[letter: min(letter + chunk_size, len(text))]
                for letter in range(0, len(text), chunk_size-overlap)
            ]        

    return chunks
def dict_to_str(d):
    return "\n".join([f"{k}: {v}" for k, v in d.items()])

    
def handler(event, context):
    bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
    client = boto3.client('s3')
    sqs_client = boto3.client('sqs')
    textract_client = boto3.client('textract')

    url = "https://sqs.us-east-1.amazonaws.com/779846784630/ia-architecture-deployment-LoadQueue7F77D490-xDtrMI3BVMfP"
    try: 
        #print(event)
        for message in event['Records']:
            body = json.loads(message['body'])            
            images =  body["images"]
            
            # read image from s3 with textract
            chunks = []

            for image in images:
                response = client.get_object(Bucket=body["bucket"], Key=image)
                image = response['Body'].read()
                image = base64.b64encode(image).decode('utf-8')
                response = textract_client.detect_document_text(Document={'Bytes': image})
                blocks = response['Blocks']
                text = ""
                for block in blocks:
                    if block['BlockType'] == 'LINE':
                        text += block['Text']
                chunks = chunking(text)
                                
            
            
            for chunk in chunks: 
                if chunk == "" or chunk == " ":
                    continue
                chunk += " " + dict_to_str(body["metadata"])
                
                #new_chunk = ai_calls.claude_call(bedrock, prompt.context_prompt(body['text']), f"<chunk>{chunk}</chunk>", 1)
                embd = ai_calls.embed_call(bedrock, chunk)['embedding']
                #print(new_chunk)
                message_body = json.dumps({
                    "embedding" : embd,
                    "chunk" : chunk,
                    "page" : body["page"],
                    "document" : body["document_name"]
                })
                response = sqs_client.send_message(QueueUrl=url, MessageBody=message_body)                   

        return {"status": "success"}

    except Exception as e: 
        print(e)
        return {"status": "error",
        "error" : e}

    # SEND THE CHUNK TO THE DB LAMBDA
    
        