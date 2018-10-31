import json
from json_interface import Json_Interface
from pathlib import Path
import requests
from pull_yahoo_data import Yahoo_League_Data
from pull_NHL_data import NHL_Data
import datetime
import time


class Data_Cruncher(NHL_Data):
    def __init__(self, league_url, fantasy_url, creds_file):
        NHL_Data.__init__(self, league_url, fantasy_url, creds_file)
        self.team_stats = {}

        self.master_categories = {}


    def build_skeleton(self, player_types, length):
        stats_dict = {}
        skater_cats = self.master_categories['boxscore']['skater']
        goalie_cats = self.master_categories['boxscore']['goalie']
        for team in self.teams.keys():
            stats_dict[team] = {}
            for type in player_types:
                stats_dict[team][type] = {}
                if type == 'skater':
                    cats = skater_cats
                else:
                    cats = goalie_cats
                for cat in cats:
                    stats_dict[team][type][cat] = [0]*(length)

        return stats_dict

    def gen_categories_dict(self):
        categories_dict = {'boxscore': {}, 'other': []}
        categories_dict['boxscore']['skater'] = [

                #"timeOnIce",
                "assists",
                "goals",
                "shots",
                "hits",
                "powerPlayGoals",
                "powerPlayAssists",
                "penaltyMinutes",
                #"faceOffPct",
                "faceOffWins",
                "faceoffTaken",
                "takeaways",
                "giveaways",
                "shortHandedGoals",
                "shortHandedAssists",
                "blocked",
                "plusMinus",
                #"evenTimeOnIce",
                #"powerPlayTimeOnIce",
                #"shortHandedTimeOnIce"
        ]
        categories_dict['boxscore']['goalie'] = [

                "shots",
                "saves",
                "powerPlaySaves",
                "shortHandedSaves",
                "evenSaves",
                "shortHandedShotsAgainst",
                "evenShotsAgainst",
                "powerPlayShotsAgainst",
                #"decision",
                #"savePercentage",
                #"powerPlaySavePercentage",
                #"evenStrengthSavePercentage"
        ]
        categories_dict['other'] = ['points', 'games played', 'power play points' 'short-handed points']

        return categories_dict


    def date_to_int(self, date):
        return (date - self.NHL_start_date).days

    def int_to_date(self, num):
        return self.NHL_start_date + datetime.timedelta(days=num)

    def daily_update_team_stats(self, team, player_type, category, date=None):
        if not date:
            date = self.current_date()

        daily_count = 0
        for week in self.teams[team]:
            if week == 'yahoo key':
                continue
            for player in self.teams[team][week]['starters']:
                if player_type == 'goalie' and 'G' not in self.players[player]['eligible positions']:
                    continue
                if player_type == 'skater' and 'G' in self.players[player]['eligible positions']:
                    continue
                if self.date_to_string(date) in self.teams[team][week]['starters'][player]:
                    count = self.teams[team][week]['starters'][player][self.date_to_string(date)][category]
                    daily_count += count
                    print(f"{player} made {daily_count} {category} on {date}")
                    #time.sleep(0.05)
                    pass


        return daily_count


    # for now I just want goals, but I will need to pass in a dict of categories to query each run through
    def daily_update_all_teams_stats(self, player_type, categories, date=None):
        if not date:
            date = self.current_date()

        team_dict = {}
        for team in self.teams:
            team_dict[team] = {player_type: {}}

        for category in categories:
            for team in self.teams:
                team_dict[team][player_type][category] = self.daily_update_team_stats(team, player_type, category, date)

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


    fleury_stats.master_categories = fleury_stats.gen_categories_dict()

    player_types = ['skater', 'goalie']
    fleury_stats.team_stats = fleury_stats.build_skeleton(player_types, fleury_stats.date_to_int(fleury_stats.current_date))


    my_date = fleury_stats.NHL_start_date


    while my_date < fleury_stats.current_date:
        for player_type, categories in fleury_stats.master_categories['boxscore'].items():
            daily_dict = fleury_stats.daily_update_all_teams_stats(player_type, categories, my_date)

            for team in fleury_stats.team_stats:
                for category in categories:
                    fleury_stats.team_stats[team][player_type][category][fleury_stats.date_to_int(my_date)] = daily_dict[team][player_type][category]
            pass
        my_date += datetime.timedelta(days=1)

    print("v")

    my_json.dump_stats(fleury_stats, stats_json)
    pass