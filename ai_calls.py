import json 
import boto3



def claude_body(system_prompt : str, 
                query : str, 
                max_tokens : int = 4000, 
                images : list = None):
        
    content = []
    
    if images is not None:
        for iter in range(len(images)):
            content.append({"type" : "text", 
                            "text" : f"Imagen {iter+1}"}
                        )
            content.append({"type" : "image",
                            "source" : {"type": "base64",
                                        "media_type": "image/png",
                                        "data": images[iter]
                                        }
                            }
                        )
                    
    content.append({"type" : "text",
                    "text" : query
                    }
                )
    
    query = [{
        "role": "user",
        "content": content
    }]
    
    return json.dumps({              
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": query,
        "temperature": 0.0,
        
    })

def claude_call( bedrock : boto3.client, 
                system_prompt : str, 
                query : str,
                model : int = 2, 
                max_tokens : int =4000,
                images : list = None):
    
    
    if model == 1: 
        model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
    else:
        model_id = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'
    
        
    body = claude_body(system_prompt, query=query, max_tokens=max_tokens, images=images)
    
    response = bedrock.invoke_model(
        body = body,
        modelId = model_id,
        contentType = 'application/json',
        accept = 'application/json'
    )    
    response = json.loads(response['body'].read().decode('utf-8'))
    response = response['content'][0]['text']
    return response


def embed_body(chunk_message : str):
    return json.dumps({
        'inputText' : chunk_message,
        
    })


def embed_call(bedrock : boto3.client, chunk_message : str):
    
    model_id = "amazon.titan-embed-text-v2:0"
    body = embed_body(chunk_message)

    response = bedrock.invoke_model(
        body = body,
        modelId = model_id,
        contentType = 'application/json',
        accept = 'application/json'        
    )    

    return json.loads(response['body'].read().decode('utf-8'))

