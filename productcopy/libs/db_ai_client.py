import requests 
import json
from dotenv import load_dotenv
import os
import logging



# https://docs.databricks.com/en/large-language-models/llm-serving-intro.html
# https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-models/api-reference
# https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-models/api-reference#chat-message

# Load environment variables from .env file
load_dotenv()

class DBAIClient():
    def __init__(self):
        # Access an environment variable
        self.dbtoken = os.environ.get('DATABRICKS_TOKEN')
        self.db_workspace = os.environ.get('DATABRICKS_WORKSPACE')
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        self.endpoint_url = f"https://{self.db_workspace}/serving-endpoints/databricks-dbrx-instruct/invocations"
        self.ittm_api_endpoint = os.environ.get('ITTM_ENDPOINT') 
        self.reset_messages()

    def send_chat(self):
        payload = {"messages": self.messages}
        headers = {"Content-Type": "application/json"}
        self.logger.info(f"Payload: {payload}")
        response = requests.post(self.endpoint_url, headers=headers, json=payload, auth=("token", self.dbtoken))
        self.logger.info(f"Response Text: {response.text}")
        return json.loads(response.content.decode('utf-8'))

    def compile_message(self, itt_results, user_inputs):
        msg = f'gender: {user_inputs.get("gender")}, productType: {user_inputs.get("productType")}, colour: {user_inputs.get("colour")}, subcategory: {user_inputs.get("subcategory")}, usage: {user_inputs.get("usage")}, product_title: {user_inputs.get("product_title")}, description: "{itt_results}" '
        return ('user', msg)

    def add_message(self, itt_results, user_inputs):
        role, text = self.compile_message(itt_results, user_inputs)
        msg = {
            "role": role,
            "content": text
        }
        self.messages.append(msg)


    def reset_messages(self):
        self.messages = [
            {
            "role": "system",
            "content": "You are friendly, playful assistant providing a useful description of this product based on supplied characteristics. Keep your answers to 100 words or less. Do not use emojis in your response."
            }
        ]

    def image_to_text_extract(self, content):
        data = {'dataframe_records': [{'content': content}] }

        # Make the POST request
        response = requests.post(
            self.ittm_api_endpoint,
            auth=("token", self.dbtoken),
            headers={"Content-Type": "application/json"},
            json=data
        )


        return json.loads(response.content.decode('utf-8'))