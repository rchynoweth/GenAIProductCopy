import requests
from dotenv import load_dotenv
import os 
import json
import base64

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint and token
MODEL_VERSION_URI = "https://adb-984752964297111.11.azuredatabricks.net/serving-endpoints/rac_image_endpoint/invocations"
DATABRICKS_API_TOKEN = os.environ.get('DATABRICKS_TOKEN')


# create input data from image 
# https://docs.databricks.com/en/machine-learning/model-serving/score-custom-model-endpoints.html#pandas-dataframe
with open('imgs/31096.jpg', 'rb') as f:
    img_data = f.read()

img_data_base64 = base64.b64encode(img_data).decode('utf-8')
data = {'dataframe_records': [{'content': img_data_base64}] }


# Make the POST request
response = requests.post(
    MODEL_VERSION_URI,
    auth=("token", DATABRICKS_API_TOKEN),
    headers={"Content-Type": "application/json"},
    json=data
)


json.loads(response.content.decode('utf-8'))

response.status_code

