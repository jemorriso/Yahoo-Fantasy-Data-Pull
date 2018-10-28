from pathlib import Path
from pull_yahoo_data import Yahoo_League_Data
from json_interface import Json_Interface

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
    league_file = json_dir / 'master_league_data.json'

    no_rest_for_fleury = Yahoo_League_Data(league_url, base_url, creds_file)
    no_rest_for_fleury.league['scoring categories'] = no_rest_for_fleury.parse_raw_scoring_categories()
    no_rest_for_fleury.teams = no_rest_for_fleury.parse_raw_league_teams()

    my_json = Json_Interface(json_dir)
    my_json.league_dump_to_json(no_rest_for_fleury, league_file)
