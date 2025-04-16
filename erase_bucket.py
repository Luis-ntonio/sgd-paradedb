# erase all files from a s3 bucket

import boto3
import random
import os
from tqdm   import tqdm



def erase_bucket(s3_bucket, bucket_name):
    try:    
        paginator = s3_bucket.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name)
        
        files = []
        for page in pages:
            files.extend(page["Contents"])
            
        for file in tqdm(files):
            key = file["Key"]
            s3_bucket.delete_object(Bucket=bucket_name, Key=key)
            #print(f"Deleted {key}")    
            
        return files
    except Exception as e:
        print(e)
        return None
    

def count_files(s3_bucket, bucket_name):
    
    paginator = s3_bucket.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name)
    
    files = []
    for page in pages:
        files.extend(page["Contents"])
        
    return len([file for file in files if file['Key'].endswith('.pdf')])

s3_bucket = boto3.client('s3', region_name='us-east-1')
#print(count_files(s3_bucket, "sgd-rag-test"))

erase_bucket(s3_bucket, "sgd-rag-test")
