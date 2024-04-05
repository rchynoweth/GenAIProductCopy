import requests
from dotenv import load_dotenv
import logging 
import os

# Load environment variables from .env file
load_dotenv()


class DBFileHandler():
    def __init__(self):
        # Access an environment variable
        self.dbtoken = os.getenv('DATABRICKS_TOKEN')
        self.db_workspace = os.environ.get('DATABRICKS_WORKSPACE')
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()


    def upload_file(self, contents, filename, volume_base_path='/Volumes/rac_demo_catalog/productcopy_demo/uploads'):
        api_endpoint = "/api/2.0/fs/files"
        full_api_path = f"https://{self.db_workspace}{api_endpoint}{volume_base_path}/{filename}"
        self.logger.info(f'File Path: {full_api_path}')
        api_url = f"https://{self.db_workspace}{api_endpoint}{volume_base_path}/{filename}"
        payload = {
            "contents": contents.split(',')[1],
            "overwrite": True
            }
        headers = {"Content-Type": "application/octet-stream"}
        response = requests.put(api_url, headers=headers, json=payload, auth=("token", self.dbtoken))
        self.logger.info(f"File Upload Status: {response.status_code}")
        return response