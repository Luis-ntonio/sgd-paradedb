from io import BytesIO
from gmft_pymupdf import PyMuPDFDocument
from gmft.auto import CroppedTable, AutoTableDetector, AutoTableFormatter
import fitz
import gmft
import gmft.table_detection
import gmft.table_visualization
import gmft.table_function
import gmft.table_function_algorithm
import gmft.table_captioning
import gmft.pdf_bindings.bindings_pdfium
import gmft.pdf_bindings
import gmft.common
from tqdm import tqdm
import boto3
import base64

import ai_calls
from prompt import generate_table_scan_prompt, generate_image_scan_prompt
import os
import logging

from langchain_experimental.text_splitter import SemanticChunker
from langchain_aws import BedrockEmbeddings



logger = logging.getLogger()
logger.setLevel(logging.INFO)



class Preprocessor:
    """
        This class preprocesses the document for the RAG model.
        TODO: 
            - The images are not being preprocessed correctly.
        
    """
    
    
    def __init__(self, bedrock : boto3.client):
        self.bedrock = bedrock
        #self.detector = AutoTableDetector()
        #self.formatter = AutoTableFormatter()
    
    def text_in_table(self, table_bbox, text):
        if table_bbox[0] < text[0] < table_bbox[2] and table_bbox[1] < text[1] < table_bbox[3]:
            return True
        
        return False

    
    def read_document(self, doc_name, path , table_image_folder : str):
        """
            Read the document from the path and descomposes it by a tuple of (text, images, tables).            
        """
        
        #pdf = PyMuPDFDocument(path)
        pdf = fitz.open(stream=path, filetype="pdf")
        print("Arrived to open the document")
        content_per_page = []  # it lists the content by a tuple per page (text, [images_path], [tables_path])
        
        s3_bucket = boto3.client('s3', region_name='us-east-1')
        bedrock_client  = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
        bedrock_embeddings = BedrockEmbeddings(
            model_id = "amazon.titan-embed-text-v2:0",    
            client=bedrock_client)

        chunker = SemanticChunker(bedrock_embeddings, breakpoint_threshold_amount = 0.95)
        try: 
            
            metadata = pdf.metadata 
            metadata["title"] = doc_name
            logger.info(f"Metadata: {metadata}")
            
        except Exception as e:
            logger.error(f"Error reading metadata from document: {str(e)}")
            metadata = {"title": doc_name}

        for num_page, page in tqdm(enumerate(pdf)):
            #tables = self.detector.detect(page)
            print(f"Processing page {num_page}")
            try: 
                
                text = page.get_text().replace("\n", " ")
                text = chunker.split_text(" ".join(text.split()))
                
                logger.info(f"Text: {text}")
            except Exception as e:
                logger.error(f"Error reading text from page {num_page}: {str(e)}")
                raise
            
            
            images_page = pdf.get_page_images(num_page, full=True)
            
            images_paths = []
            tables_paths = []
            
            # Image detection
            if len(images_page) > 0:
                for num_image, image in enumerate(images_page):
                    image_bbox = image[0]
                    
                    base_image = pdf.extract_image(image_bbox)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    image_name = f"{table_image_folder}/image{num_image}_page{num_page}.{image_ext}"
                    images_paths.append(image_name.split("/")[1])
                    
                    # Upload image to S3
                    s3_bucket.upload_fileobj(BytesIO(image_bytes), "sgd-rag-test", image_name)
            
            # Table detection
            """if len(tables) > 0:
                for num_table, table in enumerate(tables):
                    table_bbox = table.bbox
                    table_image = table.image()
                    
                    table_image_bytes = BytesIO()
                    table_image.save(table_image_bytes, format="PNG")
                    table_image_bytes.seek(0)
                    
                    table_image_name = f"{table_image_folder}/table{num_table}_page{num_page}.png"
                    tables_paths.append(table_image_name)
                    
                    # Upload table image to S3
                    s3_bucket.upload_fileobj(table_image_bytes, "sgd-rag-test", table_image_name)
                    
                    text = [t for t in text if not self.text_in_table(table_bbox, t)]"""
            
            #text = [t[-1] for t in text]
            content = {
                "text": text,
                "metadata": metadata,
                "images": images_paths,
                "tables": tables_paths,
                "page": num_page,
            }
            content_per_page.append(content)
    
        pdf.close()
        return content_per_page
    
    
    def preprocess_table(self, context_text : str ,table_path : str):
        """
            This function calls a VLM model to preprocess the keys from a table.
        """
        with open(table_path, 'rb') as f:
            image = f.read()
            base64_encoded_image = base64.b64encode(image).decode('utf-8')
            
        response = ai_calls.claude_call(
            self.bedrock,
            system_prompt=generate_table_scan_prompt(),            
            query=f"<Contexto>{context_text}</Contexto>",
            images=[base64_encoded_image]
        )    
                
        return response
    
    
    def preprocess_image(self, context_text : str, image_path : str):
        """
            This function preprocesses the image with a VLM model.
        """
        with open(image_path, 'rb') as f:
            image = f.read()
            base64_encoded_image = base64.b64encode(image).decode('utf-8')
            
        response = ai_calls.claude_call(            
            self.bedrock,
            system_prompt=generate_image_scan_prompt(),            
            query=f"<Contexto>{context_text}</Contexto>",                
            images=[base64_encoded_image]
        )    
        
        return response 