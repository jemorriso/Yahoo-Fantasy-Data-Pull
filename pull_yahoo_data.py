from yahoo_oauth import OAuth2
import json
from pathlib import Path
import subprocess

class Yahoo_League_Data():
    def __init__(self, league_url, fantasy_url, creds_file):
        self.oauth = self.get_oauth_session("http://fantasysports.yahooapis.com/", creds_file)
        self.league = {'league info': self.parse_raw_league_data(league_url)}
        self.league_url = league_url
        self.fantasy_url = fantasy_url
        self.current_week = self.league['league info']['current_week']

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
    def parse_raw_fantasy_rosters(self, week=None):
        # cycle through each team and grab their players
        for team in self.teams:
            roster_url = self.fantasy_url + "/teams;team_keys={}/roster".format(self.teams[team]['yahoo key'])
            # default week = None gets current week's rosters
            if week:
                roster_url += ";week={}".format(week)
            response = self.oauth.session.get(roster_url, params={'format': 'json'})
            players_json = json.dumps(response.json(), indent = 4)
            players_object = json.loads(players_json)
            players_object = players_object['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']

            self.teams[team]['week {}'.format(week if week else self.current_week)] = self.update_roster_and_player_data(team, players_object)
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
