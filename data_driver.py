from pathlib import Path
from pull_yahoo_data import Yahoo_League_Data
from utils import *
import argparse
from datetime import timedelta, date
from NHL_Yahoo import NHL_Yahoo
from data_cruncher import Data_Cruncher

def date_parser(dates_string):
    if "," in dates_string:
        dates_obj = dates_string.split(",")
        # check that they are correct format
        dates_obj = [Date_Utils.string_to_date(date_string) for date_string in dates_obj]

    else:
        dates_obj = Date_Utils.string_to_date(dates_string)

    # if no exception raised, return the date / dates
    return dates_obj


def restore_basic_yahoo_object(my_JSON):
    no_rest_for_fleury = Yahoo_League_Data(creds_json=my_JSON.creds_json)

    # now try to restore basic object
    print("attempting restore basic object...")
    to_create = my_JSON.restore_data(no_rest_for_fleury, type(no_rest_for_fleury).__name__, my_JSON, basic=True)

    # if to_create is not empty, then teams or league could not be restored, so just create a new basic object.
    if to_create:
        no_rest_for_fleury = Yahoo_League_Data(**initialize_kwargs, creds_json=my_JSON.creds_json)

    return no_rest_for_fleury


def parse_single_week(league_object, my_JSON, restore, week, data_cruncher=None):
    if data_cruncher is None:
        # NHL_yahoo object needs to have week restored from yahoo still - doesn't matter if overwriting or not - consider changing flow
        if type(league_object).__name__ == 'NHL_Yahoo':
            to_create = my_JSON.restore_data(league_object, type(league_object).__name__, my_JSON, weeks=[week])
            pass

        # only try to restore when creation mode specified for restoral
        # recall that 'week' has different meaning in yahoo vs nhl_yahoo here
        if restore:
            if type(league_object).__name__ == 'Yahoo_League_Data':
                to_create = my_JSON.restore_data(league_object, type(league_object).__name__, my_JSON, weeks=[week])

            # since player info gets updated as week info gets updated, if week not stored, we go ahead and update week and thus players also
            ########## fix ############
            if week in to_create['weeks']:
                if type(league_object).__name__ == 'Yahoo_League_Data':
                    league_object.weekly_update_fantasy_teams_and_players(week)
                else:
                    league_object.weekly_update_NHL_teams_and_players(week)

                    # indicators that week has been "initialized" in terms of NHL_Yahoo
                    league_object.weeks[week]['got_dates'] = []
                    league_object.weeks[week]['got_starters_and_players_info'] = True

        # creating new default object
        else:
            if type(league_object).__name__ == 'Yahoo_League_Data':
                league_object.weekly_update_fantasy_teams_and_players(week)
            else:
                league_object.weekly_update_NHL_teams_and_players(week)

                # indicators that week has been "initialized" in terms of NHL_Yahoo
                league_object.weeks[week]['got_dates'] = []
                league_object.weeks[week]['got_starters_and_players_info'] = True

    # if data cruncher, we just need to initialize week dictionaries for the weeks in question, depending on restore
    else:
        if not restore or restore and week not in data_cruncher.crunch_dict['weeks']:
            data_cruncher.crunch_dict['weeks'][week] = data_cruncher.build_weekly_stats_dict()


def parse_multiple_weeks(league_object, my_JSON, restore, start_week, end_week, data_cruncher=None):
    start_tuple = (league_object.league['date_from_week'][start_week], start_week)
    end_tuple = (league_object.league['date_from_week'][end_week], end_week)
    sorted_weeks = sorted(league_object.league['week_from_date'].items())

    query_weeks = sorted_weeks[sorted_weeks.index(start_tuple):sorted_weeks.index(end_tuple)+1]

    for date, week in query_weeks:
        parse_single_week(league_object, my_JSON, restore, week, data_cruncher)


def parse_weeks(league_object, my_JSON, my_date_utils, restore, dates_arg, data_cruncher=None):
    # default set date to today
    if dates_arg is None:
        week = league_object.get_week(my_date_utils.session_date)
        parse_single_week(league_object, my_JSON, restore, week, data_cruncher)

    else:
        # first check if single day or date range
        dates_obj = date_parser(dates_arg)

        # single day - type is datetime.date
        if type(dates_obj) is date:
            week = league_object.get_week(dates_obj)
            parse_single_week(league_object, my_JSON, restore, week, data_cruncher)

        # date range - utils raises error if not valid dates, so no need for error checking here
        else:
            start_week = league_object.get_week(dates_obj[0])
            end_week = league_object.get_week(dates_obj[1])
            parse_multiple_weeks(league_object, my_JSON, restore, start_week, end_week, data_cruncher)


# nhl routine ensures that any week being queried is loaded, by using parse_weeks prior to this.
def parse_single_day(nhl_yahoo_object, my_date, restore, data_cruncher=None):
    week = nhl_yahoo_object.get_week(my_date)

    if data_cruncher is None:
        if not restore or restore and Date_Utils.date_to_string(my_date) not in nhl_yahoo_object.weeks[week]['got_dates']:
            nhl_yahoo_object.parse_raw_daily_schedule(my_date)
            nhl_yahoo_object.weeks[week]['got_dates'].append(Date_Utils.date_to_string(my_date))

    else:
        if not restore or restore and Date_Utils.date_to_string(my_date) not in data_cruncher.crunch_dict['weeks'][week]['got_dates']:
            data_cruncher.daily_update_teams_stats(nhl_yahoo_object, my_date)
            data_cruncher.crunch_dict['weeks'][week]['got_dates'].append(Date_Utils.date_to_string(my_date))
            pass


def parse_multiple_days(nhl_yahoo_object, start_date, end_date, restore, data_cruncher=None):

    my_date = start_date
    # inclusive endpoints
    while my_date <=  end_date:
        parse_single_day(nhl_yahoo_object, my_date, restore, data_cruncher)
        my_date += timedelta(days=1)


def parse_days(nhl_yahoo_object, my_date_utils, dates_arg, restore, data_cruncher=None):
    if dates_arg is None:
        parse_single_day(nhl_yahoo_object, my_date_utils.session_date, restore)

    else:
        dates_obj = date_parser(dates_arg)
        if type(dates_obj) is date:
            parse_single_day(nhl_yahoo_object, dates_obj, restore, data_cruncher)

        else:
            parse_multiple_days(nhl_yahoo_object, dates_obj[0], dates_obj[1], restore, data_cruncher)


def gen_cumulative_data(data_cruncher_object, restore, league_start_date, session_start_date, session_end_date):
    # if we're trying to restore, then we want to add to the cumulative data lists
    # if overwriting, we'll generate based off the newly tallied data

    # append to list that already exists
    # append method checks to see if lists already exist and if they don't it just calls method to generate new one
    if restore:
        data_cruncher_object.append_cumulative_data_lists(league_start_date, session_end_date)
        pass
    # if restore and not last date, we just default to overwrite
    # that means we want to generate lists from the tallied weekly data
    else:
        data_cruncher_object.gen_cumulative_lists_from_weeks(league_start_date, session_end_date)


def yahoo_routine(args, yahoo_dir, nhl_dir, crunch_dir, restore, my_date_utils, initialize_kwargs):
    # initialize 3 different JSON_utils objects so that we can dump what we need to each
    my_JSON = Yahoo_Utils(yahoo_dir)
    my_NHL_JSON = Yahoo_Utils(nhl_dir)
    my_data_cruncher_JSON = Yahoo_Utils(crunch_dir, teams_file='graph_data.json')

    # default behaviour (no argument passed) is try and create from stored JSON
    if restore:
        no_rest_for_fleury = restore_basic_yahoo_object(my_JSON)

    # create basic object
    else:
        no_rest_for_fleury = Yahoo_League_Data(**initialize_kwargs, creds_json=my_JSON.creds_json)


    # now basic object has been created, so add as necessary according to the given command line args
    if args['basic']:
        return

    # parse_weeks loads / creates at least one week based on dates argument.
    parse_weeks(no_rest_for_fleury, my_JSON, my_date_utils, restore, args['dates'])

    my_JSON.dump_data(no_rest_for_fleury, type(no_rest_for_fleury).__name__, my_JSON)
    my_NHL_JSON.dump_data(no_rest_for_fleury, type(no_rest_for_fleury).__name__, my_NHL_JSON, preserve=True)
    my_data_cruncher_JSON.dump_data(no_rest_for_fleury, type(no_rest_for_fleury).__name__, my_data_cruncher_JSON, crunch=True)


def nhl_routine(args, nhl_dir, yahoo_dir, restore, my_date_utils):
    my_JSON = NHL_Yahoo_Utils(nhl_dir)

    fleury_hybrid = NHL_Yahoo()
    # default mode gets player data for current day, while if dates are specified we use those dates instead.
    # every NHL_Yahoo instance must have league, teams, players, week, and NHL teams defined
    # since the goal is to pull daily boxscore data.
    # since main method first calls yahoo object with same arguments, we can be sure that the files are now there

    # overwrite takes new meaning in NHL_yahoo - means initialize from YAHOO rather than NHL_YAHOO object
    # and overwrite to NHL_yahoo. Makes sense because yahoo is the 'base' for NHL_yahoo
    # use json object that points to yahoo_dir to load from if want "new" NHL_yahoo object
    if not restore:
        my_yahoo_JSON = NHL_Yahoo_Utils(yahoo_dir)
        to_create = my_yahoo_JSON.restore_data(fleury_hybrid, type(fleury_hybrid).__name__, my_yahoo_JSON, default=True)
        pass
    else:
        to_create = my_JSON.restore_data(fleury_hybrid, type(fleury_hybrid).__name__, my_JSON, default=True)

    if to_create:
        # NHL_teams is only value that gets returned when pass default=True
        fleury_hybrid.NHL_teams = fleury_hybrid.parse_raw_NHL_teams()

    # default set date to today
    # note here now we get expected behaviour - if overwrite, I have my base yahoo structure to work with
    # - if restore, I have whatever NHL data already, so dumping won't overwrite anything I don't want it to!!!!!
    parse_weeks(fleury_hybrid, my_JSON, my_date_utils, restore, args['dates'])

    # at this point, fleury hybrid is restored, so want to pull data for selected days
    parse_days(fleury_hybrid, my_date_utils, args['dates'], restore)

    my_JSON.dump_data(fleury_hybrid, type(fleury_hybrid).__name__, my_JSON)
    return fleury_hybrid


def data_crunch_routine(args, crunch_dir, yahoo_dir, restore, my_date_utils, nhl_yahoo_object):
    my_JSON = Data_Crunch_Utils(crunch_dir)

    fleury_cruncher = Data_Cruncher()
    # initialize from stored yahoo teams data
    if not restore:
        my_yahoo_JSON = Data_Crunch_Utils(yahoo_dir)
        to_create = my_yahoo_JSON.restore_data(fleury_cruncher, type(fleury_cruncher).__name__, my_yahoo_JSON)
    else:
        to_create = my_JSON.restore_data(fleury_cruncher, type(fleury_cruncher).__name__, my_JSON)

    # these should all be created as part of "default" data cruncher object
    if to_create:
        fleury_cruncher.crunch_dict['master_categories'] = fleury_cruncher.gen_categories_dict()
        fleury_cruncher.crunch_dict['cumulative_data'] = fleury_cruncher.gen_cumulative_data_dict()
        fleury_cruncher.gen_team_themes()
        fleury_cruncher.crunch_dict['weeks'] = {}

    parse_weeks(nhl_yahoo_object, my_JSON, my_date_utils, restore, args['dates'], data_cruncher=fleury_cruncher)

    # at this point, fleury hybrid is restored, so want to pull data for selected days
    parse_days(nhl_yahoo_object, my_date_utils, args['dates'], restore, data_cruncher=fleury_cruncher)

    # now create master cumulative data lists for each team.
    dates_obj = date_parser(args['dates'])
    if type(dates_obj) is date:
        session_start_date = session_end_date = dates_obj
    else:
        session_start_date = dates_obj[0]
        session_end_date = dates_obj[1]

    gen_cumulative_data(fleury_cruncher, restore, nhl_yahoo_object.NHL_start_date, session_start_date, session_end_date)

    my_JSON.dump_data(fleury_cruncher, type(fleury_cruncher).__name__, my_JSON)


def error_check(args):
    if args['mode'] and args['mode'] != 'overwrite' and args['mode'] != 'restore':
        raise ValueError("valid --mode arguments: \"overwrite\" and \"restore\"")

    if args['basic'] and args['basic'] != 'yahoo':
        raise ValueError("valid --basic argument: only \"yahoo\". nhl_yahoo does not have basic object.")

    if args['object'] and args['object'] != 'yahoo' and args['object'] != 'nhl':
        raise ValueError("valid --object arguments: \"yahoo\" and \"nhl\"")

    # dates are already checked in string_to_date method

    if args['basic'] and args['object'] != 'yahoo':
        raise ValueError("can't have basic nhl object.")

    if args['basic'] and args['dates']:
        raise ValueError("basic object doesn't have dates associated with it.")



if __name__=='__main__':

    command_line_args = argparse.ArgumentParser()
    command_line_args.add_argument("-m", "--mode", help="""object creation mode -
                                                            \toverwrite:\t creates new object from scratch (overwrites any previously stored data at specified location)
                                                            \trestore:\t tries to restore from specified files. If not stored, then builds those parts from scratch
                                                            """)
    command_line_args.add_argument("-b", "--basic", action='store_true', help="""only for yahoo - no argument, just option 
                                                            \tcreates new yahoo object from constructor only, or restores from JSON to same degree
                                                            """)
    command_line_args.add_argument("-o", "--object", help="""type of object to be created - \n
                                                             \tyahoo:\t creates yahoo league data object
                                                             \tnhl:\t creates nhl_yahoo object
                                                             """)
    command_line_args.add_argument("-d", "--dates", help="""allows for range of dates to be selected, or single day - \n
                                                            \trange should be specified as follows: \"YYYY/MM/DD,YYYY/MM/DD\")
                                                            \tendpoints are inclusive
                                                            \tif yahoo object, converts dates to weeks to query
                                                            \tif nhl yahoo object, goes day by day
                                                            \tsingle day format: \"YYYY/MM/DD\"
                                                            """)
    command_line_args.add_argument("-c", "--crunch", action='store_true', help="""also crunch the data that is retrieved from yahoo / NHL; option only""")

    args = vars(command_line_args.parse_args())
    error_check(args)

    project_dir = Path.cwd()
    #json_dir = project_dir / 'JSON-data'
    yahoo_dir = project_dir / 'Yahoo-data'
    nhl_dir = project_dir / 'NHL-data'
    crunch_dir = project_dir / 'Graph-data'

    if not yahoo_dir.exists():
        yahoo_dir.mkdir()

    if not nhl_dir.exists():
        nhl_dir.mkdir()

    if not crunch_dir.exists():
        crunch_dir.mkdir()

    my_date_utils = Date_Utils()
    restore = True if args['mode'] == 'restore' or args['mode'] is None else False


    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    initialize_kwargs = {'league_url': league_url,
                         'fantasy_url': base_url,
                         'initialize': True,
                         'long_weeks': [1, 16]
                         }

    # first call yahoo routine with same args to ensure that NHL routine has something to load from!
    # this always gets called so actually we don't need the args check
    yahoo_routine(args, yahoo_dir, nhl_dir, crunch_dir, restore, my_date_utils, initialize_kwargs)

    # default object is of type NHL_Yahoo
    if args['object'] == 'nhl' or args['object'] is None:
        # need NHL object for data_cruncher
        fleury_hybrid = nhl_routine(args, nhl_dir, yahoo_dir, restore, my_date_utils)

    if args['crunch']:
        data_crunch_routine(args, crunch_dir, yahoo_dir, restore, my_date_utils, fleury_hybrid)

