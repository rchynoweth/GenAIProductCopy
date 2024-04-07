import requests
import os 
import json
import base64
import urllib.request

def test_api():

    # Define the API endpoint and token
    MODEL_VERSION_URI = "https://adb-984752964297111.11.azuredatabricks.net/serving-endpoints/rac_image_endpoint/invocations"
    DATABRICKS_API_TOKEN = os.environ.get('DATABRICKS_TOKEN')

    # create input data from image 
    with open('./13682.jpg', 'rb') as f:
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
    print(response.text)
    assert response.status_code == 200