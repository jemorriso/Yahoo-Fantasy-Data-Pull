import json
from utils import Json_Interface
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

        self.graph_data = {}

        self.dates = {}

        self.team_themes = {}

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

    def build_themes_dict(self):
        theme_dict = {}
        for team in self.teams.keys():
            theme_dict[team] = {'font': "", 'colour': ""}
        return theme_dict

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


    def gen_dates_list(self, start_date, end_date):
        num_days = (end_date - start_date).days
        return [start_date + datetime.timedelta(days=x) for x in range(0, num_days)]


    def gen_cumulative_data_list(self, team, player_type, stat):
        sum = 0
        data_list = []
        for datapoint in self.team_stats[team][player_type][stat]:
            data_list.append(sum + datapoint)
            sum += datapoint

        return data_list

    def gen_team_themes(self):
        colours_dict = {"Chabot Shalom": "#0038b8",         # israeli flag blue
                        "Easy Kreider": "#002868",          # american flag blue
                        "Hotline Kling": "#bae1ff",         # pastel blue
                        "Jeremy Morrison": "#6F2DA8",       # grape
                        "Just a Quickie": "#B2F302",        # lime
                        "Malkin My Way DT": "#FFB612",      # pittsburgh steelers gold
                        "Marchand did 9/11": "#58595B",     # smokey grey
                        "MyFreeCams Talbot": "#008000",     # green
                        "Papa D's hot sawce": "#FF8C00",    # habanero orange
                        "Phil Special": "#c68958",          # bread colour
                        "Red Light District": "#e9241d",    # fire engine red
                        "half clapper": "#0A7E8C"           # metallic seaweed
                        }
        for team in colours_dict:
            self.team_themes[team]['colour'] = colours_dict[team]


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

    my_json.restore_stats(fleury_stats, stats_json)



    my_date = fleury_stats.NHL_start_date


    while my_date < fleury_stats.current_date:
        for player_type, categories in fleury_stats.master_categories['boxscore'].items():
            daily_dict = fleury_stats.daily_update_all_teams_stats(player_type, categories, my_date)

            for team in fleury_stats.team_stats:
                for category in categories:
                    fleury_stats.team_stats[team][player_type][category][fleury_stats.date_to_int(my_date)] = daily_dict[team][player_type][category]
            pass
        my_date += datetime.timedelta(days=1)


    for category in fleury_stats.master_categories['boxscore']['skater']:
        fleury_stats.graph_data[category] = {}
        for team in fleury_stats.teams.keys():
            fleury_stats.graph_data[category][team] = fleury_stats.gen_cumulative_data_list(team, 'skater', category)


    #
    # fleury_stats.team_themes = fleury_stats.build_themes_dict()
    # fleury_stats.gen_team_themes()
    #
    # fleury_stats.master_categories = fleury_stats.gen_categories_dict()
    #
    # player_types = ['skater', 'goalie']
    # fleury_stats.team_stats = fleury_stats.build_skeleton(player_types, fleury_stats.date_to_int(fleury_stats.current_date))
    #
    #

    #
    # date_list = fleury_stats.gen_dates_list(fleury_stats.NHL_start_date, fleury_stats.current_date-datetime.timedelta(days=1))
    # fleury_stats.dates = [fleury_stats.date_to_string(date) for date in date_list]
    #
    #
    #
    # fleury_stats.graph_data['goals'] = {}
    # for team in fleury_stats.teams.keys():
    #     fleury_stats.graph_data['goals'][team] = fleury_stats.gen_cumulative_data_list(team, 'skater', 'goals')
    #
    #
    my_json.dump_stats(fleury_stats, stats_json)
    pass