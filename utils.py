import json
from datetime import datetime, date, timedelta
from pathlib import Path


class Date_Utils:
    def __init__(self):
        self.session_date = date.today()

    @staticmethod
    def date_to_string(my_date):
        try:
            return my_date.strftime("%Y-%m-%d")
        except TypeError:
            print(f"object {my_date} is not a datetime object.")


    @staticmethod
    def string_to_date(my_string):
        try:
            if "/" in my_string:
                return datetime.strptime(my_string, "%Y/%m/%d").date()
            else:
                return datetime.strptime(my_string, "%Y-%m-%d").date()
        except ValueError:
            print(f"string {my_string} cannot be converted into datetime object.")


    # used for data cruncher conversions
    @staticmethod
    def date_to_int(start_date, end_date):
        return (end_date - start_date).days


    @staticmethod
    def int_to_date(start_date, num):
        return start_date + timedelta(days=num)


    @staticmethod
    def gen_dates_list(start_date, end_date):
        num_days = (end_date - start_date).days
        return [start_date + timedelta(days=x) for x in range(0, num_days)]



class JSON_interface:

    # both NHL and Yahoo league objects will dump to / retreive data from the JSON files initialized here.
    # def __init__(self, json_dir):
    #     self.json_dir = json_dir
    #
    #     # no use initializing weekly files since they will be accessed and created on the fly
    #     self.league_json = self.json_dir / 'league.json'
    #     self.players_json = self.json_dir / 'players.json'
    #     self.teams_json = self.json_dir / 'teams.json'


    # interface function to both NHL and yahoo
    def dump_data(self, league_object, league_type, my_JSON, **kwargs):
        if league_type == 'Yahoo_League_Data':
            my_JSON.dump_yahoo_data(league_object, **kwargs)

        elif league_type == 'NHL_Yahoo':
            my_JSON.dump_nhl_yahoo(league_object, **kwargs)

        elif league_type == 'Data_Cruncher':
            my_JSON.dump_data_cruncher(league_object)


    # interface function to both NHL and yahoo
    def restore_data(self, league_object, league_type, my_JSON, **kwargs):
        if league_type == 'Yahoo_League_Data':
            return my_JSON.restore_yahoo_data(league_object, **kwargs)

        elif league_type == 'NHL_Yahoo':
            return my_JSON.restore_nhl_yahoo(league_object, **kwargs)

        elif league_type == 'Data_Cruncher':
            return my_JSON.restore_data_cruncher(league_object)


    def write_json(self, python_object, json_file):
        with open(json_file, "w+") as write_file:
            json.dump(python_object, write_file, indent=2, sort_keys=True)


    def read_json(self, json_file):
        with open(json_file, "r") as read_json:
            return json.load(read_json)


class Data_Crunch_Utils(JSON_interface):
    def __init__(self, json_dir):
        self.json_dir = json_dir
        self.graph_json = json_dir / 'graph_data.json'

    def restore_data_cruncher(self, data_cruncher_object):
        # data_driver ensures that NHL_Yahoo object is already there; all we need to do is operate on it...
        to_create = {}

        # rely on yahoo object to deliver team names before we try to crunch data
        try:
            data_cruncher_object.crunch_dict = self.read_json(self.graph_json)
        except FileNotFoundError:
            print(f"{self.graph_json} does not exist. Create yahoo object with desired parameters first")

        try:
            data_cruncher_object.crunch_dict['master_categories']
            data_cruncher_object.crunch_dict['weeks']
        except KeyError:
            print("default data cruncher object does not exist. Creating...")
            to_create['default'] = True

        return to_create


    def dump_data_cruncher(self, data_cruncher_object):
        self.write_json(data_cruncher_object.crunch_dict, self.graph_json)


class NHL_Yahoo_Utils(JSON_interface):
    def __init__(self, json_dir):
        self.json_dir = json_dir

        # no use initializing weekly files since they will be accessed and created on the fly
        self.league_json = self.json_dir / 'league.json'
        self.players_json = self.json_dir / 'players.json'
        self.teams_json = self.json_dir / 'teams.json'

        self.NHL_json = self.json_dir / 'NHL_teams.json'


    def restore_nhl_yahoo(self, league_object, **kwargs):
        to_create = {}

        # always restore league, teams, and players
        # keep structure similar to Yahoo_Utils so I can create Yahoo League Data object first if I need to

        # this should always get called after yahoo object call, for now enforce by throwing errors below
        if 'default' in kwargs:
            try:
                league_object.league = self.read_json(self.league_json)
                league_object.teams = self.read_json(self.teams_json)
                league_object.players = self.read_json(self.players_json)
            except FileNotFoundError:
                print(f"{self.league_json}, {self.teams_json} or {self.players_json} does not exist. Create yahoo object with desired parameters first")

            try:
                league_object.NHL_teams = self.read_json(self.NHL_json)
            except FileNotFoundError:
                print(f"{self.NHL_json} does not exist. Creating...")
                to_create['NHL_teams'] = True

        ############ CHECK ON TRY /EXCEPT FLOW #########
        if 'weeks' in kwargs:
            to_create['weeks'] = []
            for week in kwargs['weeks']:
                week_json = self.json_dir / '{}.json'.format(week)
                try:
                    league_object.weeks[week] = self.read_json(week_json)
                except FileNotFoundError:
                    print(f"{week}.json does not exist. Create yahoo object with desired parameters first")

                # if try restore NHL_Yahoo for 1st time for certain week, days list won't exist, so need to return indicator to create
                # likewise for got_starters_and_player_info
                ##### assuming here that they always go together
                try:
                    league_object.weeks[week]['got_dates']
                    league_object.weeks[week]['got_starters_and_players_info']
                except KeyError:
                    print(f"got_days list does not yet exist for {week}. Creating...")
                    print(f"Haven't yet updated team starters or checked for player info for {week}. Will run weekly_update_NHL_teams_and_players...")
                    to_create['weeks'].append(week)

        return to_create


    # dummy used for copying files from yahoo to NHL before calling NHL - only overwrite if nothing there.
    # since only default yahoo object can become NHL, if league DNE, then league, teams and players DNE, so write them all
    def dump_nhl_yahoo(self, fantasy_league):
        self.write_json(fantasy_league.league, self.league_json)
        self.write_json(fantasy_league.teams, self.teams_json)
        self.write_json(fantasy_league.players, self.players_json)

        # shouldn't get called before real NHL object gets created.
        self.write_json(fantasy_league.NHL_teams, self.NHL_json)

        for week in fantasy_league.weeks:
            week_json = self.json_dir / '{}.json'.format(week)
            self.write_json(fantasy_league.weeks[week], week_json)


# we create an object of type Yahoo_Utils, which inherits the methods of JSON_interface.
# then only call methods in JSON_interface; Yahoo_Utils implements the interface.
class Yahoo_Utils(JSON_interface):
    def __init__(self, json_dir, teams_file=False):
        self.json_dir = json_dir
        self.creds_json = self.json_dir / 'oauth_credentials.json'

        # no use initializing weekly files since they will be accessed and created on the fly
        self.league_json = self.json_dir / 'league.json'
        self.players_json = self.json_dir / 'players.json'

        # add the ability to specify teams file name, since I want to initialize data cruncher
        if not teams_file:
            self.teams_json = self.json_dir / 'teams.json'
        else:
            self.teams_json = self.json_dir / teams_file

    # preserve is used for dumping yahoo data to NHL directory - we don't want to overwrite any NHL data that's there
    # so set preserve to true in that case
    # preserve never needs to be set to true for yahoo - just use option restore.
    def dump_yahoo_data(self, fantasy_league, preserve=False, crunch=False):
        # crunch specifies we're dumping data to initialize teams for data cruncher folder...
        # this solution isn't ideal but I don't want to create an entire class for initializing data cruncher from Yahoo
        # so just add a simple check here
        if crunch:
            self.dump_yahoo_for_data_cruncher(fantasy_league)
            return

        # league and teams always get created together
        if not preserve or preserve and not self.league_json.exists():
            self.write_json(fantasy_league.league, self.league_json)
            self.write_json(fantasy_league.teams, self.teams_json)

        if fantasy_league.players:
            if not preserve or preserve and not self.players_json.exists():
                self.write_json(fantasy_league.players, self.players_json)

        if fantasy_league.weeks:
            for week in fantasy_league.weeks:
                week_json = self.json_dir / '{}.json'.format(week)
                if not preserve or preserve and not week_json.exists():
                    self.write_json(fantasy_league.weeks[week], week_json)


    # data cruncher needs to be initialized with teams from yahoo, ** we should actually keep team keys in all of them if team name changes
    # don't need other stuff since data cruncher doesn't really build on yahoo
    # since data cruncher will operate on NHL_yahoo object we'll keep it minimal here
    def dump_yahoo_for_data_cruncher(self, fantasy_league):
        if not self.teams_json.exists():
            # turn it into correct format for data cruncher
            data_cruncher_dict = {'teams': fantasy_league.teams}
            self.write_json(data_cruncher_dict, self.teams_json)


    def restore_yahoo_data(self, league_object, **kwargs):
        to_create = {}
        if 'basic' in kwargs:
            try:
                league_object.league = self.read_json(self.league_json)
                league_object.teams = self.read_json(self.teams_json)
                print("successfully restored basic object")
            except FileNotFoundError:
                print(f"{self.league_json} or {self.teams_json} does not exist. Will create new basic object...")
                to_create['basic'] = True

        # if 'players' in kwargs:
        #     try:
        #         league_object.players = self.read_json(self.players_json)
        #     except FileNotFoundError:
        #         print(f"{self.players_json} does not exist. Will create new attribute...")
        #         to_create['players'] = True

        # recall that players and weeks go hand in hand.
        # in pull_yahoo, whenever weeks updated, so is master players list
        # so if I have to update weeks, then I will update players
        # its still useful to print a message saying that players_json will be created.
        if 'weeks' in kwargs:
            to_create['weeks'] = []
            try:
                league_object.players = self.read_json(self.players_json)
            except FileNotFoundError:
                ######## its not possible for week to exist without players, so no need to add to to_create ######
                print(f"{self.players_json} does not exist. Will create new attribute...")

            for week in kwargs['weeks']:
                week_json = self.json_dir / '{}.json'.format(week)
                try:
                    league_object.weeks[week] = self.read_json(week_json)
                except FileNotFoundError:
                    print(f"{week}.json does not exist. Will create new attribute...")
                    to_create['weeks'].append(week)

        return to_create