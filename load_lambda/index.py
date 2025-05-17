"""import json
import os
import logging
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# PostgreSQL config
postgres = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = int(os.getenv("POSTGRES_PORT", 5432))
database = os.getenv("POSTGRES_DB")
schema_name = os.getenv("SCHEMA_NAME", "public")
table_name = os.getenv("TABLE_NAME", "test_table")

def insert_chunk(body):
    try:
        conn = psycopg2.connect(
            dbname=database,
            user=postgres,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()

        embedding = body['embedding']
        chunk = body['chunk']
        page = body['page']
        document = body['document']
        upload_datetime = datetime.now()

        cur.execute(f'''
            INSERT INTO {schema_name}.{table_name}
            (document, page, chunk, tsv, embedding, upload_datetime)
            VALUES (%s, %s, %s, to_tsvector('english', %s), %s, %s)
        ''', (document, page, chunk, chunk, embedding, upload_datetime))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Inserted chunk from document: {document}, page: {page}")

    except Exception as e:
        logger.error(f"❌ Error inserting into PostgreSQL: {str(e)}")
        raise

def handler(event, context):
    try:
        for record in event['Records']:
            body = json.loads(record['body'])
            insert_chunk(body)

        return {
            'statusCode': 200,
            'body': json.dumps('Document chunks stored successfully in PostgreSQL')
        }

    except Exception as e:
        logger.error(f"❌ Error in handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing request: {str(e)}')
        }
"""

import json
import os
import logging
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# OpenSearch configuration from environment variables
OPENSEARCH_HOST = "search-sgd-rag-test-oy7oksnwsjazwv3mt5lxr4fz7q.us-east-1.es.amazonaws.com"  # Replace with your OpenSearch domain endpoint
OPENSEARCH_PORT = 443  # Default HTTPS port for OpenSearch
OPENSEARCH_INDEX = "document_chunks"  # Replace with your OpenSearch index name

# AWS credentials for SigV4 authentication
AWS_REGION = "us-east-1"  # Replace with your AWS region

def get_opensearch_client():
    """
    Create and return an OpenSearch client with SigV4 authentication.
    """
    try:
        # Get AWS credentials
        session = boto3.Session()
        credentials = session.get_credentials()

        # Create AWS4Auth object for SigV4 authentication
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            AWS_REGION,
            "es",  # Service name for OpenSearch
            session_token=credentials.token
        )

        # Create OpenSearch client
        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=60
        )
        return client
    except Exception as e:
        logger.error(f"Error connecting to OpenSearch: {str(e)}")
        raise

def process_message(message, opensearch_client):
    """
    Process a message and insert it into OpenSearch.
    """
    try:
        body = json.loads(message['body'])
        
        # Extract fields from the message
        embedding = body['embedding']
        chunk = body['chunk']
        page = body['page']
        document = body['document']
        label = body['label']
        upload_datetime = datetime.now().isoformat()

        # Create a document to insert into OpenSearch
        document_body = {
            "document": document,
            "page": page,
            "chunk": chunk,
            "embedding": embedding,
            "label": label,
            "upload_datetime": upload_datetime
        }

        # Insert the document into OpenSearch
        response = opensearch_client.index(
            index=OPENSEARCH_INDEX,
            body=document_body,
            refresh=False  # Refresh the index to make the document searchable immediately
        )

        logger.info(f"Successfully inserted chunk from document: {document}, page: {page}")
        logger.info(f"OpenSearch response: {response}")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise

def handler(event, context):
    """
    Lambda function handler.
    """
    opensearch_client = None
    try:
        # Connect to OpenSearch
        opensearch_client = get_opensearch_client()

        # Process each record in the event
        for record in event['Records']:
            process_message(record, opensearch_client)

        return {
            'statusCode': 200,
            'body': json.dumps('Document chunks and embeddings stored successfully in OpenSearch')
        }

    except Exception as e:
        logger.error(f"Error in Lambda handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing request: {str(e)}')
        }

    finally:
        # Close the OpenSearch client
        if opensearch_client:
            opensearch_client.close()