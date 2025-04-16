
# take a random number of pdf files from a s3 bucket and upload them to another s3 bucket
# %% 
import boto3
import random
import os
import fitz
from tqdm   import tqdm
from dotenv import load_dotenv
# Load environment variables from a .env file
load_dotenv()

# Access environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

s3_bucket = boto3.client('s3', region_name='us-east-1')

def random_pdf_files(s3_bucket, bucket_name, num_files):
    
    paginator = s3_bucket.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name)
    total_files = 0 
    
    pdfs_less_6 = []
    with open("pdfs.txt", "r") as f:
        pdfs_less_6 = f.readlines()
    
    pdfs_less_6 = [pdf.strip() for pdf in pdfs_less_6]
    for page in pages:        
        files = page['Contents']
    
    
        files = [file for file in files if file['Key'].endswith('.pdf')]
        print(f"Number of pdf files: {len(files)}")
        
        for file in tqdm(files):
            
            
            
            
            
            file_name = file['Key']
            destination_bucket = f"Documentos/{file_name.split('/')[-1]}"
            
            # read file from s3
            #s3_bucket.download_file(bucket_name, file_name, "temp.pdf")
            
            if file_name in pdfs_less_6:                            
                s3_bucket.copy_object(Bucket="sgd-rag-test", CopySource={"Bucket": bucket_name, "Key": file_name}, Key=destination_bucket)
                total_files += 1           
            
            
            if total_files == num_files:
                return total_files
            
    return total_files


def identify_all_less_6_pages(s3_bucket, bucket_name, max = 10000):
    paginator = s3_bucket.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name)
    total_files = 0 
    
    pdfs_less_6 = []
    with open("pdfs.txt", "w") as f:
        for page in pages:        
            files = page['Contents']
            files = [file for file in files if file['Key'].endswith('.pdf')]
            print(f"Number of pdf files: {len(files)}")
            
            for file in tqdm(files):
                file_name = file['Key']
                # read file from s3
                s3_bucket.download_file(bucket_name, file_name, "temp.pdf")
                try: 
                    pdf = fitz.open("temp.pdf")
                    if len(pdf) < 6:
                        pdfs_less_6.append(file_name)
                        f.write(f"{file_name}\n")
                        total_files += 1
                    
                    os.remove("temp.pdf")
                    
                    if total_files == max:
                        return pdfs_less_6
                except Exception as e:
                    print(f"Error reading file {file_name}: {str(e)}")
                    os.remove("temp.pdf")
                    continue
                
    return pdfs_less_6

def download_files_from_s3(s3_bucket, bucket_name, num_files):
    paginator = s3_bucket.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name)
    total_files = 0 
    for page in pages:        
        files = page['Contents']
        files = [file for file in files if file['Key'].endswith('.pdf')]
        print(f"Number of pdf files: {len(files)}")
        
        for file in tqdm(files):
            total_files += 1
            file_name = file['Key']
            destination_bucket = f"./Documentos/{file_name.split('/')[-1]}"
            s3_bucket.download_file(bucket_name, file_name, destination_bucket)
            
            if total_files == num_files:
                return total_files
            
    return total_files

#pdfs_less_6 = identify_all_less_6_pages(s3_bucket, "inaigem-sgd-data")
print(f"{random_pdf_files(s3_bucket, 'inaigem-sgd-data', 2000)} files were uploaded to sgd-rag-test/Documentos/")
#print(f"{download_files_from_s3(s3_bucket, 'inaigem-sgd-data', 2000)}") 
#files were downloaded to sgd-rag-test/Documentos/")


