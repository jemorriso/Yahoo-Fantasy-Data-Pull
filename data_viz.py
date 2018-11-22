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
@app.route('/')
def index():

    return render_template('index.html')


# then I can have diff pages for diff types of information to convey
@app.route('/graphs')
def graphs():

    return render_template('line_chart3.html', title='Hotline goals', max=60, labels=date_list, values=goal_list)



if __name__ == '__main__':

    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    git_dir = Path.cwd()
    json_dir = git_dir / 'JSON_data'
    creds_json = json_dir / 'oauth_creds.json'
    league_json = json_dir / 'master_league_data.json'
    stats_json = json_dir / 'master_data_crunch.json'

    my_json = Json_Interface(json_dir)

    fleury_stats = Data_Cruncher(league_url, base_url, creds_json)
    #my_json.restore_league_from_json(fleury_stats, league_json, NHL=True)
    my_json.restore_stats(fleury_stats, stats_json)

    goal_list = fleury_stats.graph_data['goals']['Hotline Kling']
    date_list = fleury_stats.dates

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

    pass

