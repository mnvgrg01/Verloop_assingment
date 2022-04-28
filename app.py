#Web Framework - a collection of libraries or modules that helps in developing web applications.

import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import json
import os

from flask import Flask,render_template,request,current_app
from constants import BASE_GOOGLE_LOCATION_API_ENDPOINT

app = Flask(__name__)
logger = logging.getLogger(__name__)


def lat_long(query: dict):
    """
    Returns output for a given address in either JSON or XML format.

    query(dict):
        dict having info about address of location and the type of output requested by end user.

    return:
        Response object

    """

    response_output_type = query['output_format']
    api_resp = None

    try:
        endpoint= f'{BASE_GOOGLE_LOCATION_API_ENDPOINT}/{response_output_type}'
        add = {
            'address':query['address'],
            'key':_get_api_key(),
        }
        url_add = urlencode(add)
        url = f'{endpoint}?{url_add}'
        api_resp = requests.get(url)
    except Exception as e:
        error_msg = f"Some error occurred while querying google API - {e}"
        logger.error(error_msg)
        return error_msg

    # success status code
    if api_resp.status_code in range(200,299):
        if response_output_type == 'json':
            try:
                location_data = api_resp.json()['results'][0]['geometry']['location']
                address_data = api_resp.json()['results'][0]['formatted_address']
                data = {'coordinates':location_data,'address':address_data}
                response_json = json.dumps(
                    data,
                    allow_nan = True,
                    indent = 4
                )
            except Exception as e:
                err_msg = f"Some error occurred while parsing google api response - {e}"
                logger.error(err_msg)
                return err_msg
            return current_app.response_class(response_json,mimetype="application/json")
        elif response_output_type == 'xml':
            try:
                bs_data = BeautifulSoup(api_resp.text,'xml')
                add_xml = bs_data.find('formatted_address').text
                lat_xml = bs_data.find('lat').text
                long_xml = bs_data.find('lng').text
                root = ET.Element('root')
                add = ET.SubElement(root,'address')
                cord = ET.SubElement(root,'cordinates')
                lat = ET.SubElement(cord,'lat')
                lng = ET.SubElement(cord,'lng')
                lat.text = lat_xml
                lng.text = long_xml
                add.text = add_xml
            except Exception as e:
                err_msg = f"Some error occurred while parsing google api response - {e}"
                logger.error(err_msg)
                return err_msg
            return current_app.response_class(ET.tostring(root,encoding='utf8',method='xml'),mimetype="application/xml")
        return "Un-supported output format provided by user"
    return "Error occurred while hitting Google API"

def _get_api_key() -> str:
    """
    Returns google API key from environment variable
    :return: string
    """
    VERLOOP_GOOGLE_API_KEY = os.environ.get('VERLOOP_GOOGLE_API_KEY', '')
    return VERLOOP_GOOGLE_API_KEY
        
@app.route('/',methods = ['GET'])
def index_page():
    return render_template('index.html')

@app.route('/getAddressDetails',methods = ['POST'])
def getAddressDetails():
    if request.method == 'POST':
        address = request.form['address']
        type_format = request.form['type_format']
        query_dict = {'address':address,'output_format':type_format}
        result = lat_long(query_dict)
    else:
        return "Request method not allowed."
    return result

if __name__ == '__main__':
    app.run()
