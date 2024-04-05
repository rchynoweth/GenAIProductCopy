from databricks import sql 
from dotenv import load_dotenv
import logging 
import os

# Load environment variables from .env file
load_dotenv()


class DBSQLClient():
    def __init__(self):
        # Access an environment variable
        self.dbtoken = os.getenv('DATABRICKS_TOKEN')
        self.server_hostname = os.environ.get('DATABRICKS_WORKSPACE')
        self.http_path = os.environ.get('WAREHOUSE_HTTP_PATH')
        self.catalog_name = os.environ.get('DATABRICKS_CATALOG')
        self.schema_name = os.environ.get('DATABRICKS_SCHEMA')
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

        
    def execute_query(self, query):
        with sql.connect(server_hostname=self.server_hostname, 
                        http_path=self.http_path, 
                        access_token=self.dbtoken) as connection:
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()

        return result


    def get_schemas(self):
        return self.execute_query("SHOW SCHEMAS")


    def create_product_upload_table(self):
        sql_qry = f"""
        create table if not exists {self.catalog_name}.{self.schema_name}.product_uploads (
            image_to_text_output STRING,
            image_path STRING,
            llm_description STRING,
            gender STRING,
            category STRING,
            subcategory STRING,
            product_type STRING,
            colour STRING,
            usage STRING,
            product_title STRING
        ) 
        """
        return self.execute_query(query=sql_qry)


    def insert_product_upload_data(self, fields):
        sql_qry = f"""
        insert into {self.catalog_name}.{self.schema_name}.product_uploads (image_to_text_output, image_path, llm_description, gender, category, subcategory, product_type, colour, usage, product_title)
        values (
            "{fields.get('image_to_text_output')}",
            "{fields.get('image_path')}",
            "{fields.get('llm_description')}",
            "{fields.get('gender')}",
            "{fields.get('category')}",
            "{fields.get('subcategory')}",
            "{fields.get('product_type')}",
            "{fields.get('colour')}",
            "{fields.get('usage')}",
            "{fields.get('product_title')}"
        );
        """
        return self.execute_query(sql_qry)