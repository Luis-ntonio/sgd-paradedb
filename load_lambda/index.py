import json
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

        cur.execute(f"""
            INSERT INTO {schema_name}.{table_name}
            (document, page, chunk, tsv, embedding, upload_datetime)
            VALUES (%s, %s, %s, to_tsvector('english', %s), %s, %s)
        """, (document, page, chunk, chunk, embedding, upload_datetime))

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
