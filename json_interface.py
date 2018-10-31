import json
from pathlib import Path

class Json_Interface():
    def __init__(self, dir):
        self.directory = dir

    def league_dump_to_json(self, fantasy_league, league_json, NHL=False):
        league_object = {}
        league_object['league name'] = fantasy_league.league['league info']['name']
        league_object['weekly starting dates'] = fantasy_league.weekly_start_dates
        league_object.update(fantasy_league.league)
        league_object['teams'] = fantasy_league.teams
        if fantasy_league.players:
            league_object['players'] = fantasy_league.players

        if NHL:
            if fantasy_league.NHL_teams:
                league_object['NHL teams'] = fantasy_league.NHL_teams

        self.write_json(league_object, league_json)
        pass



    def restore_league_from_json(self, fantasy_league, league_json, NHL=False):
        league_object = self.read_json(league_json)
        fantasy_league.league['scoring categories'] = league_object['scoring categories']
        fantasy_league.weekly_start_dates = league_object['weekly starting dates']
        fantasy_league.teams = league_object['teams']
        if 'players' in league_object:
            fantasy_league.players = league_object['players']

        if NHL:
            if 'NHL teams' in league_object:
                fantasy_league.NHL_teams = league_object['NHL teams']

        return fantasy_league



    def dump_stats(self, fantasy_league, stats_json):
        stats_object = {}
        stats_object['team stats'] = fantasy_league.team_stats
        stats_object['master categories'] = fantasy_league.master_categories
        self.write_json(stats_object, stats_json)


    def restore_stats(self, fantasy_league, stats_json):
        stats_object = self.read_json(stats_json)
        fantasy_league.team_stats = stats_object['team stats']
        return fantasy_league


    def write_json(self, python_object, json_file):
        with open(json_file, "w+") as write_file:
            json.dump(python_object, write_file, indent=4)


    def append_json(self, python_object, json_file):
        with open(json_file, "a") as write_file:
            json.dump(python_object, write_file, indent=4)


    def read_json(self, json_file):
        if not json_file.exists():
            print("{} not found.".format(json_file))
            exit(1)
        with open(json_file, "r") as read_json:
            return json.load(read_json)