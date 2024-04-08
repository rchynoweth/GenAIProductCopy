# Databricks notebook source
# MAGIC %md The purpose of this notebook is to extract descriptions from images as part of  with the Product Description Generation solution accelerator.  This notebook was developed on a **Databricks ML 14.3 LTS GPU-enabled** cluster with Standard_NC24ads_A100_v4. 

# COMMAND ----------

# MAGIC %md ##Introduction
# MAGIC
# MAGIC In this notebook, we will generate basic descriptions for each of the images read in the prior notebook.  These descriptions will serve as a critical input to our final noteobook.

# COMMAND ----------

dbutils.widgets.text('catalog_name', '')
dbutils.widgets.text('schema_name', '')

catalog_name = dbutils.widgets.get('catalog_name')
schema_name = dbutils.widgets.get('schema_name')

# COMMAND ----------

spark.sql(f"use catalog {catalog_name}")
spark.sql(f"use schema {schema_name}")

# COMMAND ----------

import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature
from mlflow import MlflowClient

mlflow.set_registry_uri('databricks-uc')

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy to Model Serving 

# COMMAND ----------

from mlflow.deployments import get_deploy_client

client = get_deploy_client("databricks")

# COMMAND ----------

mlflow_client = MlflowClient()
reg_models = mlflow_client.search_model_versions(f"name = '{catalog_name}.{schema_name}.rac_t5_small_fine_tune_product_copy'")
reg_models

# COMMAND ----------

model_name = "rac_t5_small_fine_tune_product_copy"
full_model_name = f"{catalog_name}.{schema_name}.{model_name}"
model_version = reg_models[-1].version
endpoint_name = "rac_copy_generation_endpoint"

# COMMAND ----------

try: 
  client.get_endpoint(endpoint=endpoint_name)
  endpoint_exists = True
except:
  endpoint_exists = False

# COMMAND ----------

endpoint_config = {
          "served_entities": [
              {
                  "name": f"{model_name}-{model_version}",
                  "entity_name": full_model_name,
                  "entity_version": model_version,
                  "workload_size": "Small",
                  "workload_type": "GPU_LARGE",
                  "scale_to_zero_enabled": True,
              }
          ],
          "auto_capture_config": {
              "catalog_name": catalog_name,
              "schema_name": schema_name,
              "table_name_prefix": model_name,
          },
          "traffic_config": {
              "routes": [
                  {
                      "served_model_name": f"{model_name}-{model_version}",
                      "traffic_percentage": 100,
                  }
              ]
          },
      }

# COMMAND ----------

if endpoint_exists == False:
  endpoint = client.create_endpoint(
      name=endpoint_name,
      config=endpoint_config,
  )
else :
  del endpoint_config['auto_capture_config']
  endpoint = client.update_endpoint(
    endpoint=endpoint_name,
    config=endpoint_config,
    )

# COMMAND ----------


