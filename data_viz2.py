import json
from utils import Json_Interface
from pathlib import Path
from data_cruncher import Data_Cruncher
import datetime
import time
from flask import Flask, render_template
import os



app = Flask(__name__)


# by convention, base called index.html
@app.route('/', methods=['GET', 'POST'])
def index():

    return render_template('helloworld.html')
    pass

# then I can have diff pages for diff types of information to convey
@app.route('/graphs')
def graphs():

    json_file = './JSON_data/master_data_crunch.json'
    with open(json_file, "r") as read_json:
        graph_data = json.load(read_json)

    return render_template('cumulative_data.html', data=graph_data)

    pass


if __name__ == '__main__':


    app.run(debug=True)

    pass

