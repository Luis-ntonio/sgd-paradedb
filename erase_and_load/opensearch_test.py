import boto3    

from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
import ai_calls
import os 

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

endpoint ="search-search-sgd-rag-tst-xq2prgvmk76osh6de5w6yq5jci.us-east-1.es.amazonaws.com"
region = "us-east-1"
service = "es"
# opensearch
# Open7286_


# environment variables



AWS_ACCESS_KEY_ID= os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY= os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN= os.getenv('AWS_SESSION_TOKEN')

print(f"AWS_ACCESS_KEY_ID : {AWS_ACCESS_KEY_ID} \n AWS_SECRET_ACCESS_KEY : {AWS_SECRET_ACCESS_KEY} \n AWS_SESSION_TOKEN : {AWS_SESSION_TOKEN}")

aws_auth = AWS4Auth( AWS_ACCESS_KEY_ID,  AWS_SECRET_ACCESS_KEY,  region,  service, session_token=AWS_SESSION_TOKEN)
                    

client = OpenSearch(
    hosts = [{'host': endpoint, 'port': 443}],
    http_auth = aws_auth,
    connection_class = RequestsHttpConnection,
    use_ssl = True,
    ssl_show_warn = True, 
    verify_cert = True,
    timeout=60
)

if client.ping():
    print('Connected to OpenSearch')
else:
    
    print(f'OpenSearch domain not responding. Check your configuration. {client.info()}')
    
    
    
index_name = "document_chunks"



index_body = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 312,  # Tune this parameter based on your needs
            "refresh_interval": "100s"
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "document": {
                "type": "text",
                "analyzer": "standard"
            },
            "page": {"type": "integer"},
            "chunk": {
                "type": "text",
                "analyzer": "standard",
                "index_options": "docs"  # Minimal indexing if you don't need positions/offsets

            },
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "name": "hnsw",
                    "space_type": "innerproduct",
                    "engine": "faiss",
                    "parameters": {
                        "ef_construction": 650,
                        "m": 32,
                    }
                }
            },
            "label": {
                "type": "keyword"
            },
            "upload_datetime": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            }
        }
    }
}

if not client.indices.exists(index_name):
    client.indices.create(index=index_name, body=index_body)
    print(f"Index {index_name} created")
else:
    client.indices.delete(index=index_name)
    client.indices.create(index=index_name, body=index_body)
    print(f"Index {index_name} deleted and created again")

