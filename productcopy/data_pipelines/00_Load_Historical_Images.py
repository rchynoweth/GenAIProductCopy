# Databricks notebook source
# MAGIC %md The purpose of this notebook is to load the dataset that will be used with the Product Description Generation solution accelerator.  This notebook was developed on a **Databricks ML 14.3 LTS GPU-enabled** cluster.

# COMMAND ----------

# MAGIC %md ##Introduction
# MAGIC
# MAGIC In this first notebook, we will read both product metadata and product images into persisted tables.  These tables will provide us access to the data needed for subsequent notebooks in the accelerator.
# MAGIC
# MAGIC The dataset we are using is the [e-commerce product images dataset](https://www.kaggle.com/datasets/vikashrajluhaniwal/fashion-images) available on Kaggle.  The dataset is provided under a public domain Creative Commons 1.0 license and consists of 2,900 product images and associated product metadata.
# MAGIC
# MAGIC Before running this accelerator, the files associated with this dataset should be uploaded to an [external volume](https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/volumes) you have configured within your environment.  
# MAGIC
# MAGIC In the cell below, please edit the volume path to the appropriate volume directory. 

# COMMAND ----------

spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# COMMAND ----------

# Only run this command once to unzip the files
# %sh

# cd /Volumes/rac_demo_catalog/productcopy_demo/ecomm_product_images/ # this is the path of the folder where the zip file resides
# unzip /Volumes/rac_demo_catalog/productcopy_demo/ecomm_product_images/archive.zip 



# COMMAND ----------

import os
dbrx_endpoint_url = "https://adb-984752964297111.11.azuredatabricks.net/serving-endpoints/rac_image_endpoint/invocations"
dbtoken = os.environ.get('DATABRICKS_TOKEN')

# COMMAND ----------

# data_path = "/Volumes/rac_demo_catalog/productcopy_demo/ecomm_product_images/"
# catalog_name = 'rac_demo_catalog'
# schema_name = 'productcopy_demo'
dbutils.widgets.text('data_path', '')
dbutils.widgets.text('catalog_name', '')
dbutils.widgets.text('schema_name', '')

data_path = dbutils.widgets.get('data_path')
catalog_name = dbutils.widgets.get('catalog_name')
schema_name = dbutils.widgets.get('schema_name')

# COMMAND ----------

spark.sql(f"use catalog {catalog_name}")
spark.sql(f"use schema {schema_name}")

# COMMAND ----------

# DBTITLE 1,Import Required Libraries
from pyspark.sql.functions import *
import json
import requests

# COMMAND ----------

def get_description(gender, productType, colour, category, subcategory, usage, product_title):
  messages = [
              {
              "role": "system",
              "content": "You are friendly, playful assistant providing a useful description of this product based on supplied characteristics. Keep your answers to 100 words or less. Do not use emojis in your response."
              }, 
              {
              "role": "user",
              "content": f'gender: {gender}, productType: {productType}, colour: {colour}, subcategory: {subcategory}, category: {category}, usage: {usage}, product_title: {product_title}'
            }
          ]

  payload = {"messages": messages}
  headers = {"Content-Type": "application/json"}
  try :
    response = requests.post(dbrx_endpoint_url, headers=headers, json=payload, auth=("token", dbtoken))
    content = json.loads(response.content.decode('utf-8'))
    return content.get('choices')[0].get('message').get('content')
  except :
    return None

# COMMAND ----------

desc_udf = udf(get_description)

# COMMAND ----------

# MAGIC %md ##Step 1: Load Image Data
# MAGIC
# MAGIC To load the images into a persisted table, we will recursively read the contents starting with the base-level folder associated with our dataset.  We will limit the data we upload to those files with a *jpg* extension as this is consistent with the contents of the downloaded dataset:

# COMMAND ----------

# DBTITLE 1,Product Images
# read jpg image files
images = (
  spark
    .read
    .format("binaryFile") # read file contents as binary
    .option("recursiveFileLookup", "true") # recursive navigation of folder structures
    .option("pathGlobFilter", "*.jpg") # read only files with jpg extension
    .load(f"{data_path}/data") # starting point for accessing files
  )

# write images to persisted table
_ = (
  images
    .write
    .mode("overwrite")
    .format("delta")
    .saveAsTable("product_images")
)

# display data in table
display(
  spark
    .read
    .table("product_images")
    )

# COMMAND ----------

# MAGIC %md ##Step 2: Load Product Info
# MAGIC
# MAGIC We will now read the product information found in the *fashion.csv* file associated with this dataset. 
# MAGIC
# MAGIC Notice that we are creating a description column using an LLM. Please keep in mind that this is a demo and we want a description field to "fine-tune" the LLM so in this case we are doing this. However, in a non-demo environment the descriptions would have been created by humans with specific intent and marketing language. 

# COMMAND ----------

# DBTITLE 1,Read Product Metadata
# read metadata file
info = (
  spark
    .read
    .format("csv")
    .option("header", True)
    .option("delimiter", ",")
    .load(f"{data_path}/data/fashion.csv")
    .withColumn('BaseProductDescription', desc_udf(col('Gender'), col('ProductType'), col('Colour'), col('Category'), col('Subcategory'), col('Usage'), col('ProductTitle')))
  ) 

# display data
display(info)

# COMMAND ----------

# MAGIC %md Each product is associated with one and only one image.  The path to the specific image in the storage environment is based on the product category, and gender associated with each item.  Each file is named for the product id with which it associated.  This path was automatically captured when we read the images into a dataframe in the prior step.  Here, we will need to construct the path to provide us a key on which to link product information and the images: 

# COMMAND ----------

# DBTITLE 1,Persist with DBFS Path to Image
_= (
  info # add field for dbfs path to image file
    .withColumn('path', 
                  concat(
                  lit('dbfs:'),
                  lit(f"{data_path}/data/"), 
                  'category', lit("/"),
                  'gender', lit("/"),
                  lit("Images/images_with_product_ids/"),
                  'productid', lit('.jpg')
                )
      )
    .write # write data to persisted table
      .mode("overwrite")
      .option('overwriteSchema','true')
      .format("delta")
      .saveAsTable("product_info")
)

# review data in table
display(
  spark.table('product_info')
  )

# COMMAND ----------

# MAGIC %md ##Step 3: Examine the Data Set
# MAGIC
# MAGIC A quick review of the data reveals we have 2,906 products in our dataset and one image for each:

# COMMAND ----------

spark.sql(
"""select distinct category, subcategory
from product_info""").show()

# COMMAND ----------

# DBTITLE 1,Count of Products & Images
# MAGIC %sql 
# MAGIC
# MAGIC SELECT 
# MAGIC   COUNT(a.path) as products,
# MAGIC   COUNT(b.path) as images
# MAGIC FROM product_info a
# MAGIC FULL OUTER JOIN product_images b
# MAGIC    ON a.path=b.path

# COMMAND ----------

# MAGIC %md We can break down the data based on category and gender which may be helpful should we wish to subset our data to use different prompts or otherwise limit the scope of later steps:

# COMMAND ----------

# DBTITLE 1,Breakdown of Top-Level Categorizations
# MAGIC %sql
# MAGIC
# MAGIC SELECT 
# MAGIC   a.category,
# MAGIC   a.gender,
# MAGIC   COUNT(*) as instances
# MAGIC FROM product_info a
# MAGIC GROUP BY a.category, a.gender WITH CUBE
# MAGIC ORDER BY 1, 2;

# COMMAND ----------

# MAGIC %md © 2024 Databricks, Inc. All rights reserved. The source in this notebook is provided subject to the Databricks License. All included or referenced third party libraries are subject to the licenses set forth below.
# MAGIC
# MAGIC | library                                | description             | license    | source                                              |
# MAGIC |----------------------------------------|-------------------------|------------|-----------------------------------------------------|
# MAGIC | Transformers | State-of-the-art Machine Learning for JAX, PyTorch and TensorFlow | Apache 2.0 | https://pypi.org/project/transformers/ |
# MAGIC | Salesforce/instructblip-flan-t5-xl  | InstructBLIP model using Flan-T5-xl as language model | MIT | https://huggingface.co/Salesforce/instructblip-flan-t5-xl |
# MAGIC | Llama2-70B-Chat | A pretrained and fine-tuned generative text model with 70 billion parameters |  Meta |https://ai.meta.com/resources/models-and-libraries/llama-downloads                       |
