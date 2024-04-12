# Databricks notebook source
# MAGIC %md
# MAGIC # LLM Fine Tuning 
# MAGIC
# MAGIC Resources: 
# MAGIC - https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms
# MAGIC - https://www.databricks.com/blog/fine-tuning-large-language-models-hugging-face-and-deepspeed

# COMMAND ----------

# MAGIC %pip install datasets 

# COMMAND ----------

# MAGIC %pip install accelerate==0.29.1

# COMMAND ----------

# MAGIC %pip install rouge-score

# COMMAND ----------

# MAGIC %pip install git+https://github.com/huggingface/transformers

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

user_name = spark.sql("select current_user()").collect()[0][0]
user_name

# COMMAND ----------

import os
import re
from pyspark.sql.functions import udf

import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature

mlflow.set_registry_uri('databricks-uc')

os.environ['DATABRICKS_TOKEN'] = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
os.environ['DATABRICKS_HOST'] = "https://" + spark.conf.get("spark.databricks.workspaceUrl")
os.environ['TRANSFORMERS_CACHE'] = f"/dbfs/tmp/{user_name}/cache/hf"
os.environ['MLFLOW_EXPERIMENT_NAME'] = f"/Users/{user_name}/fine-tuning-t5"
os.environ['MLFLOW_FLATTEN_PARAMS'] = "true"

# COMMAND ----------

# catalog_name = 'rac_demo_catalog'
# schema_name = 'productcopy_demo'

dbutils.widgets.text('catalog_name', '')
dbutils.widgets.text('schema_name', '')

catalog_name = dbutils.widgets.get('catalog_name')
schema_name = dbutils.widgets.get('schema_name')

# COMMAND ----------

spark.sql(f"use catalog {catalog_name}")
spark.sql(f"use schema {schema_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load and Clean Data

# COMMAND ----------

product_info_df = spark.read.table('product_info')
display(product_info_df)

# COMMAND ----------

# Some simple (simplistic) cleaning: remove tags, escapes, newlines
# Also keep only the first N tokens to avoid problems with long reviews
remove_regex = re.compile(r"(&[#0-9]+;|<[^>]+>|\[\[[^\]]+\]\]|[\r\n]+)")
split_regex = re.compile(r"([?!.]\s+)")

def clean_text(text, max_tokens):
  if not text:
    return ""
  text = remove_regex.sub(" ", text.strip()).strip()
  approx_tokens = 0
  cleaned = ""
  for fragment in split_regex.split(text):
    approx_tokens += len(fragment.split(" "))
    if (approx_tokens > max_tokens):
      break
    cleaned += fragment
  return cleaned.strip()

@udf('string')
def clean_text_udf(text):
  return clean_text(text, 100)

# COMMAND ----------


# Pick examples that are longer
clean_product_info = (product_info_df
  .withColumn("clean_description", clean_text_udf("BaseProductDescription"))
  .filter("LENGTH(clean_description) > 0 AND LENGTH(clean_description) > 0")

)

# write data out
(clean_product_info
 .write
 .mode('overwrite')
 .format("delta")
 .saveAsTable('cleaned_product_info')
)

# COMMAND ----------

df = spark.sql("""
               select ProductTitle, clean_description as text
               from cleaned_product_info
               """)
display(df)

# COMMAND ----------

def split_dataset(df, train_ratio = 0.8, test_ratio = 0.2):
    # Perform the train-test split
    train_df, test_df = df.randomSplit([train_ratio, test_ratio], seed=42)
    return train_df, test_df

# COMMAND ----------

train_df, val_df = split_dataset(df)
train_df.toPandas().to_csv(f"/dbfs/tmp/{user_name}/train.csv", index=False)
val_df.toPandas().to_csv(f"/dbfs/tmp/{user_name}/val.csv", index=False)

# COMMAND ----------

print(f"/dbfs/tmp/{user_name}/train.csv")
print(f"/dbfs/tmp/{user_name}/val.csv")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fine Tuning Step

# COMMAND ----------

# MAGIC %sh export DATABRICKS_TOKEN && export DATABRICKS_HOST && export MLFLOW_EXPERIMENT_NAME && export MLFLOW_FLATTEN_PARAMS && python \
# MAGIC     /Workspace/Repos/ryan.chynoweth@databricks.com/GenAIProductCopy/productcopy/data_pipelines/run_summarization.py \
# MAGIC     --model_name_or_path t5-small \
# MAGIC     --do_train \
# MAGIC     --do_eval \
# MAGIC     --train_file /dbfs/tmp/ryan.chynoweth@databricks.com/train.csv \
# MAGIC     --validation_file /dbfs/tmp/ryan.chynoweth@databricks.com/val.csv \
# MAGIC     --source_prefix "summarize: " \
# MAGIC     --output_dir /dbfs/tmp/ryan.chynoweth@databricks.com/t5-small-summary \
# MAGIC     --optim adafactor \
# MAGIC     --num_train_epochs 8 \
# MAGIC     --bf16 \
# MAGIC     --per_device_train_batch_size 64 \
# MAGIC     --per_device_eval_batch_size 64 \
# MAGIC     --predict_with_generate \
# MAGIC     --run_name "t5-small-fine-tune-product-desc"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inference Code

# COMMAND ----------

df = spark.read.format("delta").table('cleaned_product_info')

# COMMAND ----------

from pyspark.sql.functions import collect_list, concat_ws, col, count, pandas_udf
from transformers import pipeline
import pandas as pd

summarizer_pipeline = pipeline("summarization",\
  model=f"/dbfs/tmp/{user_name}/t5-small-summary",\
  tokenizer=f"/dbfs/tmp/{user_name}/t5-small-summary",\
  num_beams=10, min_new_tokens=50)
summarizer_broadcast = sc.broadcast(summarizer_pipeline)

@pandas_udf('string')
def summarize_description(descriptions):
  pipe = summarizer_broadcast.value(("summarize: " + descriptions).to_list(), batch_size=8, truncation=True)
  return pd.Series([s['summary_text'] for s in pipe])



llm_output_df = (df.groupBy("ProductId")
  .agg(collect_list("clean_description").alias("desc_array"), count("*").alias("n"))
  # .filter("n >= 10")
  .select("ProductId", "n", concat_ws(" ", col("desc_array")).alias("descriptions"))
  .withColumn("descriptions", summarize_description("descriptions"))
)

display(llm_output_df.select("ProductId", "descriptions").limit(10))

# COMMAND ----------

# MAGIC %md 
# MAGIC ## Package solution for Model Serving

# COMMAND ----------

import mlflow
import torch

class CopyGenerationModel(mlflow.pyfunc.PythonModel):
  
  def load_context(self, context):
    self.pipeline = pipeline("summarization", \
      model=context.artifacts["pipeline"], tokenizer=context.artifacts["pipeline"], \
      num_beams=10, min_new_tokens=50, \
      device=0 if torch.cuda.is_available() else -1)
    
  def predict(self, context, model_input): 
    texts = ("summarize: " + model_input.iloc[:,0]).to_list()
    pipe = self.pipeline(texts, truncation=True, batch_size=8)
    return pd.Series([s['summary_text'] for s in pipe])

# COMMAND ----------

# MAGIC %sh rm -r /tmp/t5-small-summary ; mkdir -p /tmp/t5-small-summary ; cp /dbfs/tmp/ryan.chynoweth@databricks.com/t5-small-summary/* /tmp/t5-small-summary

# COMMAND ----------

reqs = ["git+https://github.com/huggingface/transformers","datasets", "accelerate==0.29.1","rouge-score"]
mlflow.set_experiment(f"/Users/{user_name}/fine-tuning-t5")
content_list = ["This is a input string for the model."]
pdf = pd.DataFrame({'content': content_list})
api_output = "This is an output description for a product."

with mlflow.start_run(run_name = "rac_t5_small_fine_tune_product_copy"):
  model_name = 'rac_t5_small_fine_tune_product_copy'
  run = mlflow.active_run()
  signature = infer_signature(pdf, api_output, None)

  mlflow.pyfunc.log_model(artifacts={"pipeline": "/tmp/t5-small-summary"}, 
    artifact_path="rac_t5_small_fine_tune_product_copy", 
    python_model=CopyGenerationModel(),
    signature=signature, 
    pip_requirements=reqs)
  
  model_uri = f"runs:/{run.info.run_id}/{model_name}"
  mlflow.register_model(model_uri=model_uri, name=f"{catalog_name}.{schema_name}.rac_t5_small_fine_tune_product_copy", await_registration_for=600)

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC # Conclusion
# MAGIC In those notebook we sourced and cleaned our source data, fine-tuned an LLM, and packaged the LLM as a custom model to be deployed on model serving. This model can then be deployed as a real-time endpoint! Check the `Models` and `Endpoints` tabs to the left in Databricks.
