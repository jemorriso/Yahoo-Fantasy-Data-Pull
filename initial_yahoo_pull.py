from yahoo_oauth import OAuth2
import json
from pathlib import Path
from pull_yahoo_data import Yahoo_Data

############
# For the initial pull, we need to get anything that won't change over the course of the season
# Create the league, get settings, scoring categories, teams
# Then export the result to JSON file for later use
############

if __name__=="__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    git_dir = Path.cwd()
    json_dir = git_dir / 'JSON_data'
    creds_file = json_dir / 'oauth_creds.json'

    no_rest_for_fleury = Yahoo_Data(league_url, base_url, creds_file)
    no_rest_for_fleury.get_scoring_categories(league_url)
    no_rest_for_fleury.teams = no_rest_for_fleury.get_league_teams(league_url)

    no_rest_for_fleury.dump_league_data(json_dir, 'master_league_data.json')
