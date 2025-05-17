import boto3    

from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
import ai_calls
import os 



endpoint ="search-search-sgd-rag-tst-xq2prgvmk76osh6de5w6yq5jci.us-east-1.es.amazonaws.com"
region = "us-east-1"
service = "es"
# opensearch
# Open7286_


AWS_ACCESS_KEY_ID= os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY= os.environ['AWS_SECRET_ACCESS_KEY']
AWS_SESSION_TOKEN= os.environ['AWS_SESSION_TOKEN']
credentials = boto3.Session().get_credentials()
#print(credentials.access_key, credentials.secret_key, credentials.token)
aws_auth = AWS4Auth( AWS_ACCESS_KEY_ID,  AWS_SECRET_ACCESS_KEY,  region,  service, session_token=AWS_SESSION_TOKEN)
                    

client = OpenSearch(
    hosts = [{'host': endpoint, 'port': 443}],
    http_auth = aws_auth,
    connection_class = RequestsHttpConnection,
    use_ssl = True,
)

if client.ping():
    print('Connected to OpenSearch')
else:
    
    print(f'OpenSearch domain not responding. Check your configuration. {client.info()}')
    
    
    
index_name = "document_chunks"
# select all registers
response = client.search(index=index_name, body={"query": {"match_all": {}}})
print(f"Number of documents in {index_name}: {response['hits']['total']['value']}")
print(response['hits']['total'])