from pathlib import Path
from pull_yahoo_data import Yahoo_League_Data
from json_interface import Json_Interface
from pull_NHL_data import NHL_Data
import datetime

#########
# FLOW:
# call initial yahoo pull to get league data
# then get yahoo sets all the weekly rosters, updates players from yahoo
# then get nhl builds from get yahoo, and adds all the NHL team data and NHL player ids

def test_schedule_and_boxscore(no_rest_for_fleury):
    my_date = no_rest_for_fleury.start_date
    end_date = no_rest_for_fleury.end_date
    my_week = 1
    current_week = no_rest_for_fleury.current_week
    current_date = no_rest_for_fleury.current_date

    while my_date < current_date:
        print(my_date)
        my_day = my_date.weekday()
        if my_day == 0:
            if not my_date in no_rest_for_fleury.long_weeks.values():
                my_week += 1

        my_date += datetime.timedelta(days=1)

    no_rest_for_fleury.parse_raw_daily_schedule()
    no_rest_for_fleury.parse_raw_boxscore(2018020150)

def get_NHL(no_rest_for_fleury):
    # create basic object so that I can get current week's data from the server, then rebuild the rest of the object from stored JSON data

    # recreate league from stored info rather than querying server each time
    no_rest_for_fleury = my_json.restore_league_from_json(no_rest_for_fleury, league_json, NHL=True)
    no_rest_for_fleury.NHL_teams = no_rest_for_fleury.parse_raw_NHL_teams()

    current_date = datetime.date.today()

    query_dates = sorted(no_rest_for_fleury.weekly_start_dates)
    for date in query_dates:
        if date > current_date:
            break
        print(date)
        no_rest_for_fleury.update_NHL_teams_starters(date)
        no_rest_for_fleury.check_for_player_ids(date)
        my_json.league_dump_to_json(no_rest_for_fleury, league_json, NHL=True)

        pass

def get_yahoo():
    # create basic object so that I can get current week's data from the server, then rebuild the rest of the object from stored JSON data
    no_rest_for_fleury = Yahoo_League_Data(league_url, base_url, creds_json)

    # recreate league from stored info rather than querying server each time
    no_rest_for_fleury = my_json.restore_league_from_json(no_rest_for_fleury, league_json)

    current_date = datetime.date.today()

    query_dates = sorted(no_rest_for_fleury.weekly_start_dates)
    # go week by week and see how the players method works
    for date in query_dates:
        if date > current_date:
            break
        print(date)
        no_rest_for_fleury.parse_raw_fantasy_rosters(date)
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
    #get_yahoo()

    no_rest_for_fleury = NHL_Data(league_url, base_url, creds_json)
    get_NHL(no_rest_for_fleury)

    #test_schedule_and_boxscore(no_rest_for_fleury)
