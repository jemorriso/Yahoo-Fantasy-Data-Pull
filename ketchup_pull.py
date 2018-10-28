from pathlib import Path
from pull_yahoo_data import Yahoo_League_Data
from json_interface import Json_Interface
from pull_NHL_data import NHL_Data

def get_NHL():
    # create basic object so that I can get current week's data from the server, then rebuild the rest of the object from stored JSON data
    no_rest_for_fleury = NHL_Data(league_url, base_url, creds_json)

    # recreate league from stored info rather than querying server each time
    no_rest_for_fleury = my_json.restore_league_from_json(no_rest_for_fleury, league_json, NHL=True)
    no_rest_for_fleury.NHL_teams = no_rest_for_fleury.parse_raw_NHL_teams()

    for i in range(1, 4):
        no_rest_for_fleury.update_NHL_teams_starters(i)
        my_json.league_dump_to_json(no_rest_for_fleury, league_json, NHL=True)
        pass

    no_rest_for_fleury.mass_parse_player_ids()
    my_json.league_dump_to_json(no_rest_for_fleury, league_json, NHL=True)


def get_yahoo():
    # create basic object so that I can get current week's data from the server, then rebuild the rest of the object from stored JSON data
    no_rest_for_fleury = Yahoo_League_Data(league_url, base_url, creds_json)


    # recreate league from stored info rather than querying server each time
    no_rest_for_fleury = my_json.restore_league_from_json(no_rest_for_fleury, league_json)

    # go week by week and see how the players method works
    for i in range(1, 4):
        no_rest_for_fleury.parse_raw_fantasy_rosters(i)
        my_json.league_dump_to_json(no_rest_for_fleury, league_json)
        pass

if __name__=="__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    git_dir = Path.cwd()
    json_dir = git_dir / 'JSON_data'
    creds_json = json_dir / 'oauth_creds.json'
    league_json = json_dir / 'master_league_data.json'

    my_json = Json_Interface(json_dir)
    get_yahoo()
    get_NHL()
