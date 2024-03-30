# GenAI Product Copy

This repository is an end to end demo of generating product descriptions based on images. It requires multiple deep learning and LLM models to translate image to text and create a new draft copy. This demo is based on the [blog](https://www.databricks.com/blog/scaling-product-copy-creation-generative-ai) and [solution accelerator](https://databricks-industry-solutions.github.io/product_copy_genai/#product_copy_genai.html) created by Tristen Wentling and Bryan Smith from Databricks. 

![](https://cms.databricks.com/sites/default/files/inline-images/db-941-blog-img-1.png)



## Install and Run Application 

You will need to have the following `.env` file to connect to Databricks from your local desktop. 
```
DATABRICKS_TOKEN=<PAT TOKEN>
DATABRICKS_WORKSPACE=<Databricks Workspace URL> #adb-<workspaceid>.<##>.azuredatabricks.net
WAREHOUSE_HTTP_PATH=<SQL Warehouse Path> # /sql/1.0/warehouses/<ID>
DATABRICKS_CATALOG=<catalog with forecast data>
DATABRICKS_SCHEMA=<schema with forecast data>
```


To run the application locally please execute the following commands. Please note that you will need to comment out the first two lines of the [__init__.py](timeseries_ai/libs/__init__.py) file as it is coupled with the Databricks job that requires PySpark and I do not install
```
# Create environment 
conda create -n timeseriesai python=3.10

conda activate timeseriesai

# install requirements 
pip install -r requirements.txt

# change working directory and run application
cd timeseries_ai

python run_app.py
```