from yahoo_oauth import OAuth2
import json
from pathlib import Path
from datetime import datetime, timedelta
from utils import Date_Utils

# this class should only have methods in it that are related to pulling yahoo data, and processing it.
class Yahoo_League_Data:
    def __init__(self, **kwargs):

        self.oauth = self.get_oauth_session("http://fantasysports.yahooapis.com/", kwargs['creds_json'])

        # the major components of the league are defined as object attributes that are dictionaries
        self.league = {}
        self.teams = {}
        self.players = {}
        self.weeks = {}

        # # we want to restore league from json file, so go to JSON object and do this league's restoral and return
        # if 'restoral' in kwargs:
        #     print('restoring Yahoo League object....')
        #     if 'JSON_object' not in kwargs:
        #         print('error, need to restore to json object - use JSON_object in kwargs')
        #         exit(1)
        #     my_JSON = kwargs['JSON_object']
        #     my_JSON.restore_data(self, type(self).__name__, my_JSON, basic=True)


        # to make it easy, assume that each object either initializes league, scoring categories, weeks, and teams, or loads those from stored JSON
        if 'initialize' in kwargs:
            print('initializing Yahoo League object....')
            if 'league_url' not in kwargs or 'fantasy_url' not in kwargs or 'creds_json' not in kwargs:
                print("error, need to initialize league with its URL, and yahoo's fantasy url, and a credentials file generated through OAuth.")
                exit(1)

            self.league.update({'league_url': kwargs['league_url'], 'fantasy_url': kwargs['fantasy_url']})
            self.league.update({'league_info': self.parse_raw_league_data(kwargs['league_url']), 'scoring_categories': self.parse_raw_scoring_categories()})

            # set start to usual Monday, rather than Wednesday
            # design: I store any dates as strings rather than live dates, for JSON.
            my_date = Date_Utils.string_to_date(self.league['league_info']['start_date']) - timedelta(days=2)
            self.league['start_date'] = Date_Utils.date_to_string(my_date)
            my_date = Date_Utils.string_to_date(self.league['league_info']['end_date'])
            self.league['end_date'] = Date_Utils.date_to_string(my_date)

            if 'long_weeks' in kwargs:
                self.league['week_from_date'] = self.set_week_from_date(self.league['start_date'], self.league['end_date'], long_weeks=kwargs['long_weeks'])
            else:
                self.league['week_from_date'] = self.set_week_from_date(self.league['start_date'], self.league['end_date'])

            self.league['date_from_week'] = {week: date for date, week in self.league['week_from_date'].items()}

            self.teams = self.parse_raw_league_teams()



    # utilizing yahoo-oauth api
    def get_oauth_session(self, url, creds_file):
        oauth = OAuth2(None, None, from_file=creds_file, base_url=url)

        if not oauth.token_is_valid():
            oauth.refresh_access_token()

        return oauth


    # allows for queries to be made anytime during the week
    def get_week(self, date):
        sorted_weeks = sorted(self.league['week_from_date'])
        for start_date in sorted_weeks:
            if date < Date_Utils.string_to_date(start_date):
                date += timedelta(days=7)
            else:
                day_of_week = date.weekday()
                return self.league['week_from_date'][Date_Utils.date_to_string(date - timedelta(days=day_of_week))]


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
        return league_object['fantasy_content']['leagues']['0']['league'][0]


    # I have to store keys as strings rather than dates for JSON.
    def set_week_from_date(self, start_date, end_date, long_weeks=None):
        week_from_date = {}
        my_date = Date_Utils.string_to_date(start_date)
        live_end_date = Date_Utils.string_to_date(end_date)
        my_week = 1

        while my_date < live_end_date:
            if long_weeks and my_week in long_weeks:
                # 1st half
                week_from_date[Date_Utils.date_to_string(my_date)] = 'week_{}a'.format(my_week)
                # 2nd half
                my_date += timedelta(days=7)
                week_from_date[Date_Utils.date_to_string(my_date)] = 'week_{}b'.format(my_week)
            else:
                week_from_date[Date_Utils.date_to_string(my_date)] = 'week_{}'.format(my_week)
            my_week += 1
            my_date += timedelta(days=7)
            pass

        return week_from_date


    def parse_raw_scoring_categories(self):
        response = self.oauth.session.get(self.league['league_url'] + "/settings", params={'format': 'json'})

        settings_json = json.dumps(response.json(), indent=4)
        settings_object = json.loads(settings_json)
        settings_object = settings_object['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['stat_categories']['stats']

        scoring_categories= {}
        for category_dict in settings_object:
            abbreviation = category_dict['stat']['display_name']
            scoring_categories[abbreviation] = category_dict['stat']['name']

        return scoring_categories


    def parse_raw_league_teams(self):
        response = self.oauth.session.get(self.league['league_url'] + "/teams", params={'format': 'json'})

        teams_json = json.dumps(response.json(), indent=4)
        teams_object = json.loads(teams_json)
        # narrowing in on the relevant content
        teams_object = teams_object['fantasy_content']['leagues']['0']['league'][1]['teams']

        # remove count key from data pull.
        teams_object.pop('count', None)

        teams_dict = {}
        # get this bad boy: create nested dict where key is team name
        for team_dict in teams_object:
            team_name = teams_object[team_dict]['team'][0][2]['name']
            team_key = teams_object[team_dict]['team'][0][0]['team_key']
            teams_dict[team_name] = {'yahoo_key': team_key}

        return teams_dict


    def get_players_NHL_team(self, player_info):
        players_team = None

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
            else:
                raise ValueError("player X's NHL team not found. Something has gone wrong")

        # convert to NHL spelling
        if players_team == 'Montreal Canadiens':
            players_team = 'Montréal Canadiens'
        return players_team


    def get_players_eligible_positions(self, player_info):
        positions_object = None
        if 'eligible_positions' in player_info[0][12].keys():
            positions_object = player_info[0][12]['eligible_positions']
        else:
            for dict in player_info[0]:
                if 'eligible_positions' in dict.keys():
                    positions_object = dict['eligible_positions']
                    break
            else:
                raise ValueError("player X's eligible positions not found. Something has gone wrong")

        # redundant to store Util
        positions_list = []
        for x in positions_object:
            if x['position'] and not (x['position'] == 'Util' or x['position'] == 'IR'):
                positions_list.append(x['position'])
        return positions_list


    # roster must get updated every week, and its static.
    def update_roster(self, player_info, player_name, roster):
        starting_positions = ['C', 'LW', 'RW', 'D', 'G', 'Util']
        player_position = player_info[1]['selected_position'][1]['position']

        roster['starters' if player_position in starting_positions else 'bench'][player_name] = {'active_position': player_position}


    # I removed 'fantasy_team' from player, since it is prone to change, and I can easily get static weeks
    # no point in having unsure data; just access it through weekly rosters.
    def update_player(self, player_info, player):
        # if the player isn't there, just add whatever teams we have available.
        if player not in self.players:
            self.players[player] = {'last_known_NHL_team': '', 'eligible_positions': []}
            self.players[player]['last_known_NHL_team'] = self.get_players_NHL_team(player_info)
            self.players[player]['eligible_positions'] = self.get_players_eligible_positions(player_info)


    def update_roster_and_player_data(self, fantasy_team, players_object):
        roster = {'starters': {}, 'bench': {}}

        for i in range(0, players_object['count']):
            player_info = players_object[str(i)]['player']
            player_name = player_info[0][2]['name']['full']

            self.update_roster(player_info, player_name, roster)
            self.update_player(player_info, player_name)

        return roster


    # return the players that on each team, storing them as sublists for each team in Yahoo_Data teams attribute
    # efficient to only make one query for each roster, so here we also update the master player list.
    def parse_raw_fantasy_rosters(self, week):
        self.weeks[week] = {}
        self.weeks[week]['teams'] = dict.fromkeys(self.teams.keys(), {})

        # cycle through each team and grab their players
        print("Parsing weekly roster data.....")
        for team in self.teams:
            roster_url = self.league['fantasy_url'] + "/teams;team_keys={}/roster".format(self.teams[team]['yahoo_key'])
            roster_url += ";date={}".format(self.league['date_from_week'][week])

            response = self.oauth.session.get(roster_url, params={'format': 'json'})
            players_json = json.dumps(response.json(), indent = 4)
            players_object = json.loads(players_json)
            players_object = players_object['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']

            self.weeks[week]['teams'][team] = self.update_roster_and_player_data(team, players_object)
            pass
            # bench includes IR players


    # needs to be called after parse raw fantasy rosters so its packaged together in below method
    def update_weekly_starters(self, week):
        # add active players dict so that I can have constant time lookup of players when scrolling boxscores
        starters_dict = {}

        for team in self.weeks[week]['teams'].keys():
            for player in self.weeks[week]['teams'][team]['starters']:
                starters_dict[player] = team
                pass

        return starters_dict


    def weekly_update_fantasy_teams_and_players(self, week):
        self.parse_raw_fantasy_rosters(week)
        self.weeks[week]['starters'] = self.update_weekly_starters(week)