# import json
# from utils import Json_Interface
# from pathlib import Path
# import requests
# from pull_yahoo_data import Yahoo_League_Data

from datetime import timedelta

import NHL_Yahoo
from utils import Date_Utils

class Data_Cruncher():
    # constructor style factors in the fact that oftentimes we restore rather than create all new attributes.
    def __init__(self, **kwargs):
        # we only need one dictionary here; the entire object can be stored and loaded to / from JSON
        self.crunch_dict = {}


    # this function gets called whenever a new week is to be tallied; it generates the template for each week's tally
    def build_weekly_stats_dict(self):
        stats_dict = {'got_dates': [], 'teams': {}}
        skater_cats = self.crunch_dict['master_categories']['boxscore']['skater']
        goalie_cats = self.crunch_dict['master_categories']['boxscore']['goalie']
        for team in self.crunch_dict['teams']:
            stats_dict['teams'][team] = {'skater': {}, 'goalie': {}}
            for cat in skater_cats:
                stats_dict['teams'][team]['skater'][cat] = [0]*7
            for cat in goalie_cats:
                stats_dict['teams'][team]['goalie'][cat] = [0]*7

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
        categories_dict['other'] = ['points', 'games played', 'power play points', 'short-handed points']

        return categories_dict


    def gen_cumulative_data_dict(self):
        data_dict = {'teams': {}, 'last_date': None}

        # create the cumulative data lists
        categories_list = self.crunch_dict['master_categories']['boxscore']['skater'] + self.crunch_dict['master_categories']['boxscore']['goalie']
        data_dict['categories'] = categories_list

        for team in self.crunch_dict['teams']:
            data_dict['teams'][team] = {}
            for category in categories_list:
                # initialize an empty list for each category
                data_dict['teams'][team][category] = []

        return data_dict


    # def gen_teams_dict(self):
    #     self.gen_team_themes()
    #
    #     # create the cumulative data lists
    #     categories_list = self.crunch_dict['master_categories']['boxscore']['skater'] + self.crunch_dict['master_categories']['boxscore']['goalie']
    #     for team in self.crunch_dict['teams']:
    #         self.crunch_dict['teams'][team]['cumulative_data'] = {}
    #         for category in categories_list:
    #             # initialize an empty list for each category
    #             self.crunch_dict['teams'][team]['cumulative_data'][category] = []



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
            self.crunch_dict['teams'][team]['colour'] = colours_dict[team]


    def append_cumulative_data_lists(self, league_start_date, my_date):
        # we're trying to add and the data isn't there so try to create it
        if 'last_date' not in self.crunch_dict['cumulative_data']:
            self.gen_cumulative_lists_from_weeks(league_start_date, my_date)

        # its possible that we're trying to append up to a date that has already been calculated
        elif my_date < self.crunch_dict['cumulative_data']['last_date']:
            print(f"no need to generate cumulative data up to {my_date} - cumulative data up to {self.crunch_dict['cumulative_data']['last_date']} already generated.")

        # there is data that needs to be appended, and data driver has ensured that the weekly data is available
        else:



    def gen_cumulative_data_list(self, tally_list):
        sum = 0
        data_list = []
        for datapoint in tally_list:
            data_list.append(sum + datapoint)
            sum += datapoint

        return data_list


    def gen_cumulative_lists_from_weeks(self, league_start_date, my_date):

        # need to check that all dates up to start of date range / query date have been previously calculated
        # if dates up to start haven't been calculated, raise exception, since the cumulative tally won't make any sense
        self.check_tallied_dates(league_start_date, my_date)

        for category in self.crunch_dict['cumulative_data']['categories']:
            is_goalie = False
            if category in self.crunch_dict['master_categories']['boxscore']['goalie']:
                is_goalie = True
            for team in self.crunch_dict['teams']:
                assembled_weekly_list = []
                for week in self.crunch_dict['weeks']:
                    assembled_weekly_list.extend(self.crunch_dict['weeks'][week]['teams'][team]['skater' if not is_goalie else 'goalie'][category])

                # when we do weekly tallies, use day of week to determine index
                # NHL starts on a wednesday, so here we trim the first 2 leading zeroes away
                assembled_weekly_list = assembled_weekly_list[2:]
                # we also need to trim the end away since there may be trailing zeroes if entire week hasn't been filled in
                my_date_index = Date_Utils.date_to_int(league_start_date, my_date)
                assembled_weekly_list = assembled_weekly_list[:my_date_index+1]
                # add up all the numbers
                self.crunch_dict['cumulative_data']['teams'][team][category] = self.gen_cumulative_data_list(assembled_weekly_list)
                pass

        # if we got here it was successful, and we can safely say we have cumulative data up to the query date
        self.crunch_dict['cumulative_data']['last_date'] = Date_Utils.date_to_string(my_date)


    def daily_update_teams_stats(self, nhl_yahoo_object, my_date):
        week = nhl_yahoo_object.get_week(my_date)
        day_of_week = my_date.weekday()
        my_date_string = Date_Utils.date_to_string(my_date)

        for team in nhl_yahoo_object.weeks[week]['teams']:
            for player in nhl_yahoo_object.weeks[week]['teams'][team]['starters']:
                if my_date_string in nhl_yahoo_object.weeks[week]['teams'][team]['starters'][player]:
                    is_goalie = True if nhl_yahoo_object.weeks[week]['teams'][team]['starters'][player]['active_position'] == 'G' else False
                    if not is_goalie:
                        for category in self.crunch_dict['master_categories']['boxscore']['skater']:
                            self.crunch_dict['weeks'][week]['teams'][team]['skater'][category][day_of_week] += nhl_yahoo_object.weeks[week]['teams'][team]['starters'][player][my_date_string][category]

                    else:
                        for category in self.crunch_dict['master_categories']['boxscore']['goalie']:
                            self.crunch_dict['weeks'][week]['teams'][team]['goalie'][category][day_of_week] += nhl_yahoo_object.weeks[week]['teams'][team]['starters'][player][my_date_string][category]


    def check_tallied_dates(self, league_start_date, check_date):
        # build a list of all the tallied dates
        all_got_dates = []
        for week in self.crunch_dict['weeks']:
            all_got_dates.extend(self.crunch_dict['weeks'][week]['got_dates'])

        all_got_dates = [Date_Utils.string_to_date(date_string) for date_string in sorted(all_got_dates)]

        # build a list of all dates from league start date
        all_check_dates = Date_Utils.gen_dates_list(league_start_date, check_date+timedelta(days=1))

        # if there isn't an unbroken chain til the check_date, we can't tally cumulative data.
        # it doesn't really make sense to fill it all in, since that might not be what is desired.
        # so just raise an error and decide what to do after.
        for date_obj in all_check_dates:
            if date_obj not in all_got_dates:
                raise AssertionError("Not all dates up to {} have been tallied. Call data driver with date range {},{}".format(check_date, league_start_date, check_date))

