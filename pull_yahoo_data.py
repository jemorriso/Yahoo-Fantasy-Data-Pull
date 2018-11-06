from yahoo_oauth import OAuth2
import json
from pathlib import Path
import subprocess
import datetime

class Yahoo_League_Data():
    def __init__(self, league_url, fantasy_url, creds_file):
        self.oauth = self.get_oauth_session("http://fantasysports.yahooapis.com/", creds_file)
        self.league = {'league info': self.parse_raw_league_data(league_url), 'scoring categories': {}}
        self.league_url = league_url
        self.fantasy_url = fantasy_url

        # set start to usual Monday, rather than Wednesday
        self.start_date = self.string_to_date(self.league['league info']['start_date']) - datetime.timedelta(days=2)
        self.end_date = self.string_to_date(self.league['league info']['end_date'])

        # every session should have a current date since the day could roll over in the middle of execution
        self.current_date = datetime.date.today()

        # clean up below
        self.weekly_start_dates = {}

        # teams updated after object creation - can edit this?? Overloading constructors
        self.teams = {}
        # players updated while team rosters are filled out
        self.players = {}

    # utilizing yahoo-oauth api
    def get_oauth_session(self, url, creds_file):
        oauth = OAuth2(None, None, from_file=creds_file, base_url=url)

        if not oauth.token_is_valid():
            oauth.refresh_access_token()

        return oauth


    def date_to_string(self, date):
        return date.strftime("%Y-%m-%d")

    def string_to_date(self, string):
        return datetime.datetime.strptime(string, "%Y-%m-%d").date()


    # allows for queries to be made anytime during the week
    def get_week(self, date):
        sorted_weeks = sorted(self.weekly_start_dates)
        for start_date in sorted_weeks:
            if date < self.string_to_date(start_date):
                date += datetime.timedelta(days=7)
            else:
                day_of_week = date.weekday()
                return self.weekly_start_dates[self.date_to_string(date - datetime.timedelta(days=day_of_week))]


    # Can't find schedule info in API, so just hard code long weeks
    # Yahoo week 1 actually starts on Weds, but here have it start on usual Monday for convenience.
    # I have to store keys as strings rather than dates for JSON.
    def set_weekly_start_dates(self, start_date, end_date):
        weekly_start_dates = {}
        my_date = start_date
        my_week = 2

        long_weeks = {
                        "2018-10-01": 'week 1.a',
                        "2018-10-08": 'week 1.b',
                        "2019-01-21": 'week 16.a',
                        "2019-01-28": 'week 16.b'
                    }

        while my_date < end_date:
            my_date_string = self.date_to_string(my_date)
            if my_date_string in long_weeks:
                weekly_start_dates[my_date_string] = long_weeks[my_date_string]
            else:
                weekly_start_dates[my_date_string] = 'week {}'.format(my_week)
                my_week += 1
                if my_week == 16:
                    my_week += 1
            my_date += datetime.timedelta(days=7)
            pass

        return weekly_start_dates


    def parse_raw_league_data(self, url):
        # rauth utilizes python Requests module, so its a python Requests response object that is being returned.

        # decodes the response into json format
        response = self.oauth.session.get(url, params={'format': 'json'})
        league_json = (json.dumps(response.json(), indent=4))
        #print(league_json)

        # now take the json and turn it into a python object
        league_object = json.loads(league_json)
        #print(league_object)

        # grab the relevant data
        # use pycharm debugger to visualize dict nesting more easily
        return league_object['fantasy_content']['leagues']['0']['league'][0]

    def parse_raw_league_teams(self):
        response = self.oauth.session.get(self.league_url + "/teams", params={'format': 'json'})

        teams_json = json.dumps(response.json(), indent=4)
        teams_object = json.loads(teams_json)
        # narrowing in on the relevant content
        teams_object = teams_object['fantasy_content']['leagues']['0']['league'][1]['teams']

        teams_dict = {}
        # get this bad boy: create nested dict where key is team name
        for i in range(0,12):
            team_name = teams_object[str(i)]['team'][0][2]['name']
            team_key = teams_object[str(i)]['team'][0][0]['team_key']
            teams_dict[team_name] = {'yahoo key': team_key}
            # teams_dict[team_name]['key'] = team_key
        return teams_dict


    def get_players_NHL_team(self, player_info):
        # sometimes 'editorial_team_full_name' appears as a different element in the list
        # specifically, when player on IR it shows up as 7th element in list.
        # to catch other unknown cases, if its not the 5th element, just cycle through the list until you see it.
        if 'editorial_team_full_name' in player_info[0][5].keys():
            players_team = player_info[0][5]['editorial_team_full_name']
        else:
            for dict in player_info[0]:
                if 'editorial_team_full_name' in dict.keys():
                    players_team = dict['editorial_team_full_name']
                    break
        # convert to NHL spelling
        if players_team == 'Montreal Canadiens':
            players_team = 'Montréal Canadiens'
        return players_team


    def get_players_eligible_positions(self, player_info):
        if 'eligible_positions' in player_info[0][12].keys():
            positions_object = player_info[0][12]['eligible_positions']
        else:
            for dict in player_info[0]:
                if 'eligible_positions' in dict.keys():
                    positions_object = dict['eligible_positions']
                    break

        # redundant to store Util
        positions_list = []
        for x in positions_object:
            if x['position'] and not (x['position'] == 'Util' or x['position'] == 'IR'):
                positions_list.append(x['position'])
        return positions_list


    def update_roster(self, player_info, player_name, roster):
        starting_positions = ['C', 'LW', 'RW', 'D', 'G', 'Util']
        player_position = player_info[1]['selected_position'][1]['position']

        roster['starters' if player_position in starting_positions else 'bench'][player_name] = {'active position': player_position}


    def update_player(self, player_info, player, fantasy_team):
        if player not in self.players:
            self.players[player] = {'fantasy team': '', 'NHL team': '', 'eligible positions': []}
            self.players[player]['fantasy team'] = fantasy_team
            self.players[player]['NHL team'] = self.get_players_NHL_team(player_info)
            self.players[player]['eligible positions'] = self.get_players_eligible_positions(player_info)

        # the player has been traded (fantasy) or dropped and added to a different team.
        elif self.players[player]['fantasy team'] != fantasy_team:
            self.players[player]['fantasy team'] = fantasy_team

    def update_roster_and_player_data(self, fantasy_team, players_object):
        roster = {'starters': {}, 'bench': {}}

        for i in range(0, players_object['count']):
            player_info = players_object[str(i)]['player']
            player_name = player_info[0][2]['name']['full']

            self.update_roster(player_info, player_name, roster)

            ####### if player info is already stored, no need to add again.
            self.update_player(player_info, player_name, fantasy_team)

        return roster


    # return the players that on each team, storing them as sublists for each team in Yahoo_Data teams attribute
    # efficient to only make one query for each roster, so here we also update the master player list.
    def parse_raw_fantasy_rosters(self, date=None):
        # cycle through each team and grab their players
        print("Parsing weekly roster data.....")
        if not date:
            date = self.current_date
        for team in self.teams:
            roster_url = self.fantasy_url + "/teams;team_keys={}/roster".format(self.teams[team]['yahoo key'])
            roster_url += ";date={}".format(self.date_to_string(date))

            response = self.oauth.session.get(roster_url, params={'format': 'json'})
            players_json = json.dumps(response.json(), indent = 4)
            players_object = json.loads(players_json)
            players_object = players_object['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']

            self.teams[team][self.get_week(date)] = self.update_roster_and_player_data(team, players_object)
            pass
            # bench includes IR players


    def parse_raw_scoring_categories(self):
        response = self.oauth.session.get(self.league_url + "/settings", params={'format': 'json'})

        settings_json = json.dumps(response.json(), indent=4)
        settings_object = json.loads(settings_json)
        settings_object = settings_object['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['stat_categories']['stats']

        scoring_categories= {}
        for x in settings_object:
            abbreviation = x['stat']['display_name']
            scoring_categories[abbreviation] = x['stat']['name']

        return scoring_categories


if __name__=="__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    git_dir = Path.cwd()
    json_dir = git_dir / 'JSON_data'
    creds_file = json_dir / 'oauth_creds.json'

    no_rest_for_fleury = Yahoo_League_Data(league_url, base_url, creds_file)
    no_rest_for_fleury.league['scoring categories'] = no_rest_for_fleury.parse_raw_scoring_categories()
    no_rest_for_fleury.teams = no_rest_for_fleury.parse_raw_league_teams()
    no_rest_for_fleury.parse_raw_fantasy_rosters(week=1)
    print(no_rest_for_fleury.teams)
