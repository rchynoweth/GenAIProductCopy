from dash import Dash, dcc, html, Input, Output, State, callback
import logging 
from libs.db_sql_connect import DBSQLClient
from libs.db_ai_client import DBAIClient
from libs.db_filehandler import DBFileHandler
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

db_conn = DBSQLClient()
db_ai_client = DBAIClient()
db_file_client = DBFileHandler()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
options = [
    {'label': 'Girl', 'value': 'Girl'},
    {'label': 'Boy', 'value': 'Boy'},
    {'label': 'Women', 'value': 'Women'},
    {'label': 'Men', 'value': 'Men'},
    {'label': 'null', 'value': 'null'}
]

category_options = [
    {'label': 'Apparel', 'value': 'Apparel'},
    {'label': 'Footwear', 'value': 'Footwear'}
]

subcategory_options = [
    {'label': 'Topwear', 'value': 'Topwear'},
    {'label': 'Dress', 'value': 'Dress'},
    {'label': 'Sandal', 'value': 'Sandal'},
    {'label': 'Flip Flops', 'value': 'Flip Flops'},
    {'label': 'Bottomwear', 'value': 'Bottomwear'},
    {'label': 'Socks', 'value': 'Socks'},
    {'label': 'Innerwear', 'value': 'Innerwear'},
    {'label': 'Shoes', 'value': 'Shoes'},
    {'label': 'Apparel Set', 'value': 'Apparel Set'}
]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1(children='Product Copy Generator Demo', style={'textAlign':'center'}),
    dcc.Dropdown(
        id='gender',
        options=options,
        value=None,
        placeholder='Select Gender', 
        style={'margin-top': '10px'}
    ),
    dcc.Dropdown(
        id='category',
        options=category_options,
        placeholder='Select Category', 
        style={'margin-top': '10px'}
    ),
    dcc.Dropdown(
        id='subcategory',
        options=subcategory_options,
        placeholder='Select Subcategory', 
        style={'margin-top': '10px'}
    ),
    dcc.Input(id='product-type', type='text', placeholder='Product Type', style={'margin-top': '10px'}),
    dcc.Input(id='colour', type='text', placeholder='Colour', style={'margin-top': '10px'}),
    dcc.Input(id='usage', type='text', placeholder='Usage', style={'margin-top': '10px'}),
    dcc.Input(id='product-title', type='text', placeholder='Product Title', style={'margin-top': '10px'}),
    

    dcc.Upload(
        id='upload-image',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Image')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin-top': '10px'
            # 'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Button('Submit', id='submit-button', n_clicks=0, style={'width':'100%', 'text-align': 'center', 'background-color': 'blue', 'color': 'white', 'margin-top': '10px'}),
    html.Div(id='graph-text', children='Upload image to generate product analysis and description.', style={'margin-top': '10px', 'width': '100%', 'display': 'inline-block', 'textAlign': 'center', 'white-space': 'pre-wrap'}),
    html.Div(id='output-image-upload', style={'width': '100%', 'display': 'inline-block', 'textAlign': 'center', 'margin-top': '10px'}),
])

def parse_contents(contents, filename):
    # how to handle file upload??
    db_file_client.upload_file(contents=contents, filename=filename)
    logger.info(f"Upload Image Data: {filename} ")
    return html.Div([
        html.H5(f"File Name: {filename}"),

        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=contents, style={'width': '30%', 'height': 'auto', 'text-align': 'center'}),
        html.Hr(),
    ])


@app.callback(
    Output('graph-text', 'children'),  # Update the text below the graph
    [Input('upload-image', 'contents'), Input('submit-button', 'n_clicks'),Input('gender', 'value'),
        Input('category', 'value'), Input('subcategory', 'value'), Input('product-type', 'value'),
        Input('colour', 'value'), Input('usage', 'value'), Input('product-title', 'value')] 
)
def update_text(list_of_contents, n_clicks, gender, category, subcategory, product_type, colour, usage, product_title):
    logger.info(f'Rendering New Text {n_clicks}')
    logger.info(f"-------------List of contents: {list_of_contents}")

    if n_clicks:
        logger.info(f"Text Click Count = {n_clicks}")
        fields = {'gender':gender,
        'category':category,
        'subcategory':subcategory,
        'product_type':product_type,
        'colour':colour,
        'usage':usage,
        'product_title':product_title,}
        
        image_bytes = list_of_contents[0].split(",")[1]
        itt_description = db_ai_client.image_to_text_extract(image_bytes).get('predictions')
        # itt_results = db_ai_client.image_to_text_extract(contents=list_of_contents[0])
        db_ai_client.add_message(itt_results=itt_description, user_inputs=fields)
        response = db_ai_client.send_chat()
        # Return updated text when button is clicked
        text = response.get('choices')[0].get('message').get('content')
        return text



@callback(Output('output-image-upload', 'children'),
              Input('upload-image', 'contents'),
              Input('submit-button', 'n_clicks'),
              State('upload-image', 'filename'),
              State('upload-image', 'last_modified'))
def update_output(list_of_contents, list_of_dates, list_of_names, n_clicks):
    # logger.info(f"Contents: {list_of_contents}")
    logger.info(f"Names: {list_of_names}")
    logger.info(f"Dates: {list_of_dates}")
    # must add functionality to only upload file if button is clicked
    if list_of_contents is not None:
        children = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        return children

if __name__ == '__main__':
    app.run(debug=True)




### Next steps:
# 1 - Make sure that the image to text is working
# 2 - orchestrate it to call DBRX for product copy
# 3 - display everything in Web UI and allow customer to "accept" the copyright
# 4 - save everything to databricks 
# 5 - leverage an online table