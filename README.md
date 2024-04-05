# GenAI Product Copy

This repository is an end to end demo of generating product descriptions based on images. It requires multiple deep learning and LLM models to translate image to text and create a new draft copy. This demo is based on the [blog](https://www.databricks.com/blog/scaling-product-copy-creation-generative-ai) and [solution accelerator](https://databricks-industry-solutions.github.io/product_copy_genai/#product_copy_genai.html) created by Tristen Wentling and Bryan Smith from Databricks. 

![](https://cms.databricks.com/sites/default/files/inline-images/db-941-blog-img-1.png)


For the purposes of this demo I have downloaded and unzipped the contents of the [e-commerce product images dataset](https://www.kaggle.com/datasets/vikashrajluhaniwal/fashion-images?resource=download) to an imgs directory. I have not tracked this in the repo, as it is meant for adhoc uploads. This is also in line with the accelerator mentioned previously. 

Below is an example video of the resulting web application. 

https://github.com/rchynoweth/GenAIProductCopy/assets/79483287/fb4876a0-76b1-499e-bbff-715a9879ddb0

## Install and Run Application 

You will need to have the following `.env` file to connect to Databricks from your local desktop. 
```
DATABRICKS_TOKEN=<PAT TOKEN>
DATABRICKS_WORKSPACE=<Databricks Workspace URL> #adb-<workspaceid>.<##>.azuredatabricks.net
WAREHOUSE_HTTP_PATH=<SQL Warehouse Path> # /sql/1.0/warehouses/<ID>
DATABRICKS_CATALOG=<data catalog>
DATABRICKS_SCHEMA=<data schema>
ITTM_ENDPOINT=<image to text api endpoint on Databricks model serving>
```


To run the application locally please execute the following commands. 
```
# Create environment 
conda create -n productcopy python=3.10

conda activate productcopy

# install requirements 
pip install -r requirements.txt

# change working directory and run application
cd productcopy

python run_app.py
```

The entire demo includes the following steps: 
1. Ingest historical image data with product descriptions into a table 
1. Using the ingested data, we can fine tune an LLM to "stay on brand" with product descriptions. 
1. Deploy to model serving APIs for image to text and the Fine-tuned LLM
1. Run Integration tests with APIs
1. Run the Web Application. 


## Demo Inputs

The following are simply samples with data to provide during demos. The images are available in the repository as well. 

Image 31096  
- gender: Boys
- productType: Shirts
- colour: Green
- usage: Casual
- name: Palm Tree Boys Check Green Shirt
- Generated description: "The image features a green and black checkered shirt with a short sleeve and a button-down collar. The style of the shirt is casual, with a button-down collar and a short sleeve. The type of shirt is casual, with a button-down collar and a short sleeve."


Image 32554  
- gender: Men
- productType: Casual Shoes
- colour: Black
- usage: Casual
- name: Playboy Men Black Shoes
- Generated description: "The image features a pair of black leather shoes with a lace-up design and a white background. The shoes appear to be of a casual style, suitable for everyday wear."


Image 13682  
- gender: Women
- productType: Sports Shoes
- colour: Silver
- usage: Sports
- name: ADIDAS Women Duramo 3 Sports Shoes.
- Generated description: "The image depicts a pair of running shoes in a grey and blue color scheme. The shoe is labeled as a women's running shoe, which indicates that it is designed for a woman's feet. This type of shoe is typically associated with athletic activities, such as running, walking, or jogging."

Image 24985  
- gender: Girls
- productType: Tops
- colour: Pink
- usage: Casual
- name: United Colors of Benetton Kids Girls Pink Printed Top.
- Generated description: "The image features a pink t-shirt with a black and white graphic design on the front. It is a women's t-shirt, suitable for casual wear."


## Resources 

Below are various resources I have found useful: 
- https://docs.databricks.com/en/large-language-models/llm-serving-intro.html 
- https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-models/api-reference 
- https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-models/api-reference#chat-message 
- https://docs.databricks.com/api/workspace/files/upload 
- https://docs.databricks.com/en/machine-learning/model-serving/custom-models.html 
