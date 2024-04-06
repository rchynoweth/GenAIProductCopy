# Databricks notebook source
# MAGIC %md
# MAGIC # LLM Fine Tuning 
# MAGIC
# MAGIC Resources: 
# MAGIC - https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms
# MAGIC - https://www.databricks.com/blog/fine-tuning-large-language-models-hugging-face-and-deepspeed

# COMMAND ----------

# MAGIC %pip install datasets evaluate rouge-score git+https://github.com/huggingface/transformers

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

user_name = spark.sql("select current_user()").collect()[0][0]
user_name

# COMMAND ----------

import os

os.environ['DATABRICKS_TOKEN'] = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
os.environ['DATABRICKS_HOST'] = "https://" + spark.conf.get("spark.databricks.workspaceUrl")
os.environ['TRANSFORMERS_CACHE'] = f"/dbfs/tmp/{user_name}/cache/hf"
os.environ['MLFLOW_EXPERIMENT_NAME'] = f"/Users/{user_name}/fine-tuning-t5"
os.environ['MLFLOW_FLATTEN_PARAMS'] = "true"

# COMMAND ----------

catalog_name = 'rac_demo_catalog'
schema_name = 'productcopy_demo'

# COMMAND ----------

spark.sql(f"use catalog {catalog_name}")
spark.sql(f"use schema {schema_name}")

# COMMAND ----------

product_info_df = spark.read.table('product_info')
display(product_info_df)

# COMMAND ----------

def split_dataset(df, train_ratio = 0.8, test_ratio = 0.2):
    # Perform the train-test split
    train_df, test_df = df.randomSplit([train_ratio, test_ratio], seed=42)
    return train_df, test_df

# COMMAND ----------

os.removedirs(f'/dbfs/tmp/{user_name}/test')

# COMMAND ----------

os.removedirs(f'/dbfs/tmp/{user_name}/train')

# COMMAND ----------

train_df, test_df = split_dataset(product_info_df)
if os.path.exists(f'/dbfs/tmp/{user_name}/train') == False:
  print('writing train data')
  (train_df.coalesce(1).write.option("quote", "\"").mode('overwrite').format('csv').save(f'/tmp/{user_name}/train'))

if os.path.exists(f'/dbfs/tmp/{user_name}/test') == False:
  print('writing test data')
  (test_df.coalesce(1).write.option("quote", "\"").mode('overwrite').format('csv').save(f'/tmp/{user_name}/test'))

# COMMAND ----------

train_data_path = [i.path for i in dbutils.fs.ls(f'/tmp/{user_name}/train') if '.csv' in i.path][0]
print(train_data_path)

# COMMAND ----------

test_data_path = [i.path for i in dbutils.fs.ls(f'/tmp/{user_name}/test') if '.csv' in i.path][0]
print(test_data_path)

# COMMAND ----------

# MAGIC %sh export DATABRICKS_TOKEN && export DATABRICKS_HOST && export MLFLOW_EXPERIMENT_NAME && export MLFLOW_FLATTEN_PARAMS && python \
# MAGIC     /Workspace/Repos/ryan.chynoweth@databricks.com/GenAIProductCopy/productcopy/data_pipelines/run_summarization.py \
# MAGIC     --model_name_or_path t5-small \
# MAGIC     --do_train \
# MAGIC     --do_eval \
# MAGIC     --train_file /dbfs/tmp/ryan.chynoweth@databricks.com/train/part-00000-tid-2234247562327427795-2ca2c24f-c478-42a8-92fd-645ae462a62e-36-1-c000.csv \
# MAGIC     --validation_file /dbfs/tmp/ryan.chynoweth@databricks.com/test/part-00000-tid-7602695264451942812-280ce7e1-9962-4223-95a7-584693aeef9a-37-1-c000.csv \
# MAGIC     --source_prefix "summarize: " \
# MAGIC     --output_dir /dbfs/tmp/ryan.chynoweth@databricks.com/t5-small-summary \
# MAGIC     --optim adafactor \
# MAGIC     --num_train_epochs 8 \
# MAGIC     --bf16 \
# MAGIC     --per_device_train_batch_size 64 \
# MAGIC     --per_device_eval_batch_size 64 \
# MAGIC     --predict_with_generate \
# MAGIC     --run_name "t5-small-fine-tune-productcopy"

# COMMAND ----------


