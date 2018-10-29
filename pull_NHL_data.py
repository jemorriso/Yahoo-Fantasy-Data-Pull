import json
from json_interface import Json_Interface
from pathlib import Path
import requests
from pull_yahoo_data import Yahoo_League_Data
import datetime

class NHL_Data(Yahoo_League_Data):
    def __init__(self, league_url, fantasy_url, creds_file):
        Yahoo_League_Data.__init__(self, league_url, fantasy_url, creds_file)
        self.NHL_teams = None
        self.NHL_base_url = "https://statsapi.web.nhl.com/api/v1/"


    def get_player_id(self, player):

        # now is time to learn how to use grep and bash to process this JSON efficiently!! Use that saved bookmark
        for id in self.NHL_teams.keys():
            r = requests.get("https://statsapi.web.nhl.com/api/v1/teams/{}?expand=team.roster".format(id))
            team_json = json.dumps(r.json(), indent=4)
            print(team_json)
            team_object = json.loads(team_json)
            team_object = team_object[0]['id']
            # for
            # if player

        pass

    # We should not be duplicating data! I need to make a master player list
    # this will be helpful for seeing if a trade has happened
    def parse_player_id(self, player, team_object):
        roster = team_object['roster']['roster']
        for player_info in roster:
            if player_info['person']['fullName'] == player:
                self.players[player]['NHL id'] = player_info['person']['id']
                #print(f"player: {player}\nid: {self.players[player]['NHL id']}")
                return
        #print(f"{player} NOT FOUND!!!")


    # run this weekly to fill in missing player IDs
    # avoids querying each NHL team roster each week
    # needs to be called after update_NHL_teams_starters
    # better to run this on NHL teams rather than fantasy teams
    # so that if there are multiple players on a team that don't have id, only one request necessary
    def check_for_player_ids(self, date=None):
        if not date:
            date = self.current_date
        week = '{}'.format(self.get_week(date))
        team_object = None

        for team in self.NHL_teams:
            for player in self.NHL_teams[team][week]:
                # get the roster dump only for the first player on the team that needs an ID
                if 'NHL id' not in self.players[player] and not team_object:
                    team_object = self.parse_NHL_roster_dump(self.NHL_teams[team]['team id'])
                    #print(f"week: {week}")
                    self.parse_player_id(player, team_object)
                elif 'NHL id' not in self.players[player]:
                    #print(f"week: {week}")
                    self.parse_player_id(player, team_object)
            team_object = None


    def parse_NHL_roster_dump(self, id):
        r = requests.get("https://statsapi.web.nhl.com/api/v1/teams/{}?expand=team.roster".format(id))
        team_json = json.dumps(r.json(), indent=4)
        team_object = json.loads(team_json)
        return team_object['teams'][0]


    # each week, need to update list of starters, for each NHL team.
    def update_NHL_teams_starters(self, date=None):
        if not date:
            date = self.current_date
        week = '{}'.format(self.get_week(date))
        NHL_starters = self.NHL_teams
        for NHL_team in NHL_starters:
            NHL_starters[NHL_team][week] = {}
        for fantasy_team in self.teams:
            for player in self.teams[fantasy_team][week]['starters']:
                players_NHL_team = self.players[player]['NHL team']
                NHL_starters[players_NHL_team][week][player] = {'fantasy team': fantasy_team}

        self.NHL_teams = NHL_starters


    def parse_raw_NHL_teams(self):
        teams = {}

        r = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
        teams_json = json.dumps(r.json(), indent=4)
        teams_object = json.loads(teams_json)

        for i, team in enumerate(teams_object['teams']):
            # yahoo does not use accent on e in Montreal, while NHL does. Causes key error if don't fix here.
            if i == 7:
                team['name'] = 'Montreal Canadiens'
                print(teams_object['teams'][i])
            teams[team['name']] = {'team id': team['id']}

        return teams

    def parse_raw_boxscore(self, game_id):
        game_url = self.NHL_base_url + "/game/{}/boxscore".format(game_id)
        r = requests.get(game_url)
        game_json = json.dumps(r.json(), indent=4)
        game_object = json.loads(game_json)
        pass


    def parse_raw_daily_schedule(self, date=None):
        schedule_url = self.NHL_base_url + "/schedule"
        if date:
            schedule_url += "?date={}".format(date)
        r = requests.get(schedule_url)
        schedule_json = json.dumps(r.json(), indent=4)
        schedule_object = json.loads(schedule_json)
        pass


if __name__ == "__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    git_dir = Path.cwd()
    json_dir = git_dir / 'JSON_data'
    creds_json = json_dir / 'oauth_creds.json'
    league_json = json_dir / 'master_league_data.json'

    # create basic object so that I can get current week's data from the server, then rebuild the rest of the object from stored JSON data
    no_rest_for_fleury = NHL_Data(league_url, base_url, creds_json)
    my_json = Json_Interface(json_dir)

    # recreate league from stored info rather than querying server each time
    no_rest_for_fleury = my_json.restore_league_from_json(no_rest_for_fleury, league_json, NHL=True)
    no_rest_for_fleury.mass_parse_player_ids()

    pass

    # no_rest_for_fleury_NHL.get_NHL_teams()
    # print(no_rest_for_fleury_NHL.NHL_teams)
    #
    # no_rest_for_fleury_NHL.set_NHL_team_rosters('3')
    # no_rest_for_fleury_NHL.get_all_player_ids()
    # print(no_rest_for_fleury_NHL)
    # #no_rest_for_fleury_NHL.update_NHL_teams()
    # #no_rest_for_fleury_NHL.get_player_ids('2', no_rest_for_fleury_NHL.get_NHL_team_dump())