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
        self.file_api_endpoint = "/api/2.0/fs/files"

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

    def get_file_path(self, filename, volume_base_path='/Volumes/rac_demo_catalog/productcopy_demo/uploads'):
        return f"https://{self.db_workspace}{self.file_api_endpoint}{volume_base_path}/{filename}"

    def upload_file(self, contents, filename, volume_base_path='/Volumes/rac_demo_catalog/productcopy_demo/uploads'):
        full_api_path = self.get_file_path(filename=filename)
        self.logger.info(f'File Path: {full_api_path}')
        payload = {
            "contents": contents.split(',')[1],
            "overwrite": True
            }
        headers = {"Content-Type": "application/octet-stream"}
        response = requests.put(full_api_path, headers=headers, json=payload, auth=("token", self.dbtoken))
        self.logger.info(f"File Upload Status: {response.status_code}")
        return response