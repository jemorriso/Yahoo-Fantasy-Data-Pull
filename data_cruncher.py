import json
from json_interface import Json_Interface
from pathlib import Path
import requests
from pull_yahoo_data import Yahoo_League_Data
from pull_NHL_data import NHL_Data
import datetime


class Data_Cruncher(NHL_Data):
    def __init__(self, league_url, fantasy_url, creds_file):
        NHL_Data.__init__(self, league_url, fantasy_url, creds_file)
        self.team_stats = {}



    def build_skeleton(self, categories):
        for team in self.teams.keys():
            self.team_stats[team] = {}
            for category in categories:
                self.team_stats[team][category] = [0]*(self.date_to_int(self.end_date))

    def update_weekly_stats(self, category, from_date=None):
        pass


    def date_to_int(self, date):
        return (date - self.NHL_start_date).days

    def int_to_date(self, num):
        return self.NHL_start_date + datetime.timedelta(days=num)

    def daily_update_team_stats(self, team, category, date=None):
        if not date:
            date = self.current_date()

        daily_count = 0
        for week in self.teams[team]:
            if week == 'yahoo key':
                continue
            for player in self.teams[team][week]['starters']:
                if 'G' in self.players[player]['eligible positions']:
                    continue
                if self.date_to_string(date) in self.teams[team][week]['starters'][player]:
                    count = self.teams[team][week]['starters'][player][self.date_to_string(date)][category]
                    daily_count += count
                    pass

        return daily_count


    # for now I just want goals, but I will need to pass in a dict of categories to query each run through
    def daily_update_all_teams_stats(self, category, date=None):
        if not date:
            date = self.current_date()

        team_dict = {}

        for team in self.teams:
            team_dict[team] = self.daily_update_team_stats(team, category, date)

        return team_dict



if __name__ == "__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    git_dir = Path.cwd()
    json_dir = git_dir / 'JSON_data'
    creds_json = json_dir / 'oauth_creds.json'
    league_json = json_dir / 'master_league_data.json'
    stats_json = json_dir / 'master_data_crunch.json'

    my_json = Json_Interface(json_dir)


    fleury_stats = Data_Cruncher(league_url, base_url, creds_json)
    my_json.restore_league_from_json(fleury_stats, league_json, NHL=True)
    fleury_stats.build_skeleton({'goals'})


    my_date = fleury_stats.NHL_start_date


    while my_date < fleury_stats.current_date - datetime.timedelta(days=1):
        daily_dict = fleury_stats.daily_update_all_teams_stats('goals', my_date)
        for team in fleury_stats.team_stats:
            fleury_stats.team_stats[team]['goals'][fleury_stats.date_to_int(my_date)] = daily_dict[team]
        my_date += datetime.timedelta(days=1)
        pass

    my_json.dump_stats(fleury_stats, stats_json)
    pass