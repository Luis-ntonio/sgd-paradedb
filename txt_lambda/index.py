import ai_calls
import prompt
import boto3
import base64
import json


def chunking( text : str, chunk_size : int = 1000, overlap : int = 100):
        
    text = text.replace('\n', ' ')
    
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


    url = "https://sqs.us-east-1.amazonaws.com/779846784630/ia-architecture-deployment-LoadQueue7F77D490-xDtrMI3BVMfP"
    try: 
        #print(event)
        for message in event['Records']:
            body = json.loads(message['body'])
            chunks =  body["text"]
            for chunk in chunks: 
                if chunk == "" or chunk == " ":
                    continue
                chunk += " " + f" titulo : {body["metadata"]['title']}"
                #new_chunk = ai_calls.claude_call(bedrock, prompt.context_prompt(body['text']), f"<chunk>{chunk}</chunk>", 1)
                embd = ai_calls.embed_call(bedrock, chunk)['embedding']
                #print(new_chunk)
                message_body = json.dumps({
                    "embedding" : embd,
                    "chunk" : chunk,
                    "page" : body["page"],
                    "document" : body["document_name"],
                    "label" : body["document_label"]
                })
                response = sqs_client.send_message(QueueUrl=url, MessageBody=message_body)                   

        return {"status": "success"}

    except Exception as e: 
        print(e)
        return {"status": "error",
        "error" : e}

    # SEND THE CHUNK TO THE DB LAMBDA
    
        