from yahoo_oauth import OAuth2
import json
from pathlib import Path
from pull_yahoo_data import Yahoo_Data

############
# For weekly pull, we need to get list of players on active roster
# store it under team > week > players
# this script is going to run automatically every Monday.
# There are certain weeks where Monday is a continuation of last week.
# in those weeks, we DO need to get the active roster, because lineups can be edited for 2nd week of matchup
# But we should know that its the same week for tallying data
############

def week_compare():
    pass

if __name__=="__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    git_dir = Path.cwd()
    json_dir = git_dir / 'JSON_data'
    creds_json = json_dir / 'oauth_creds.json'
    league_json = json_dir / 'master_league_data.json'
    week_json = json_dir / 'master_week_data.json'
    roster_json = json_dir / 'master_roster_data.json'

    # load in the league's information
    if not league_json.exists() or not creds_json.exists():
        print("Please run initial_yahoo_pull.py to get requisite files, then run this script again")
        exit(1)

    # create basic object so that I can get current week's data from the server, then rebuild the rest of the object from stored JSON data
    no_rest_for_fleury = Yahoo_Data(league_url, base_url, creds_json)

    # recreate league from stored info rather than querying server each time
    no_rest_for_fleury_stored = no_rest_for_fleury.read_json(league_json)
    no_rest_for_fleury.teams = no_rest_for_fleury_stored['teams']
    no_rest_for_fleury.league['scoring categories'] = no_rest_for_fleury_stored['scoring categories']

    # grab the weekly roster
    # since this is automated we're always grabbing current roster
    no_rest_for_fleury.get_team_rosters(base_url)
    weekly_roster_object = no_rest_for_fleury.teams

    # update master roster data
    no_rest_for_fleury.dump_roster_data(roster_json, no_rest_for_fleury.current_week, weekly_roster_object)



    ## instead of going through all this rigamarole just make it so that if the roster data is already there for the week,
    #  assume that it's the first half of the week, and make a second half........
    # update week data
    #no_rest_for_fleury.dump_week_data(week_json)
    #week_object = no_rest_for_fleury.load_week_data(week_json)

    # I was misunderstanding. The weeks increment normally, but sometimes they are 2 week long matchups
    # But I don't care... the purpose of the project is daily updating standings

