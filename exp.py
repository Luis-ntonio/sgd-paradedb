import boto3
import fitz
import os
from langchain_experimental.text_splitter import SemanticChunker
from langchain_aws import BedrockEmbeddings




bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
bedrock_embeddings = BedrockEmbeddings(
    model_id = "amazon.titan-embed-text-v2:0",    
    client=bedrock_client)

chunker = SemanticChunker(bedrock_embeddings, breakpoint_threshold_amount = 0.5)


cwd = os.getcwd()
doc = fitz.open(os.path.join(cwd, "Documentos/20200000000002.pdf"))

# text
text = ""

for page in doc:
    text += page.get_text().replace("\n", " ")
    
    
# replace N spaces with one space
text = " ".join(text.split())

chunks = chunker.split_text(text)
print(chunker.split_text(text))
print(len(chunks))





