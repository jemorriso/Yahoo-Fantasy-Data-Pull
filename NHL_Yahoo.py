from utils import Date_Utils
from datetime import timedelta
import requests
import json

# class loads in stored data from JSON, utilizes NHL_data class, and then dumps the result back to same file
class NHL_Yahoo:
    # object needs to be initialized from stored JSON, since in its basic form it is just a Yahoo_League_Data object
    # choose not to have inheritance due to coupling and methods in Yahoo_League_Data that are strictly pertinent to that class
    def __init__(self):
        self.league = {}
        self.teams = {}
        self.players = {}
        self.weeks = {}
        self.NHL_teams = {}

        self.NHL_base_url = "https://statsapi.web.nhl.com/api/v1/"
        self.NHL_start_date = Date_Utils.string_to_date("2018-10-03")


    # allows for queries to be made anytime during the week
    def get_week(self, date):
        sorted_weeks = sorted(self.league['week_from_date'])
        for start_date in sorted_weeks:
            if date < Date_Utils.string_to_date(start_date):
                date += timedelta(days=7)
            else:
                day_of_week = date.weekday()
                return self.league['week_from_date'][Date_Utils.date_to_string(date - timedelta(days=day_of_week))]


    ##### TO DO ####
    # this method won't work for sebastian aho!
    def find_player_ID(self, player):
        r = requests.get("https://suggest.svc.nhl.com/svc/suggest/v1/minactiveplayers/{}/99999".format(player))
        player_json = json.dumps(r.json(), indent=4)
        player_object = json.loads(player_json)
        # the ID is at the end of the string with a dash in front
        player_list = player_object['suggestions'][0].split("-")

        return player_list[-1]

    # We should not be duplicating data! I need to make a master player list
    # this will be helpful for seeing if a trade has happened
    def parse_player_id(self, player, team_object):
        roster = team_object['roster']['roster']
        for player_info in roster:
            if player_info['person']['fullName'] == player:
                return player_info['person']['id']
        # the player has either been sent down, or traded. Find out the player's ID using "svc" endpoint
        # worry about what team they play for when I parse boxscores
        else:
            return self.find_player_ID(player)

    def parse_raw_player_attributes(self, id, player):
        r = requests.get("https://statsapi.web.nhl.com/api/v1/people/{}".format(id))
        attr_json = json.dumps(r.json(), indent=4)
        attr_object = json.loads(attr_json)
        print("updating player info ..... {}".format(player))
        return attr_object['people'][0]


    # run this weekly to fill in missing player IDs
    # avoids querying each NHL team roster each week
    # needs to be called after update_NHL_teams_starters
    # better to run this on NHL teams rather than fantasy teams
    # so that if there are multiple players on a team that don't have id, only one request necessary
    def check_for_player_info(self, week):
        team_object = None

        for team in self.NHL_teams:
            for player in self.NHL_teams[team]['players']:
                # get the roster dump only for the first player on the team that needs an ID
                # for starting players, we also want to get their personal info - always update ID and attributes together.
                if 'NHL_id' not in self.players[player]:
                    if not team_object:
                        team_object = self.parse_NHL_roster_dump(self.NHL_teams[team]['team_id'])
                    self.players[player]['NHL_id'] = self.parse_player_id(player, team_object)
                    self.players[player]['attributes'] = self.parse_raw_player_attributes(self.players[player]['NHL_id'], player)
            team_object = None


    def parse_NHL_roster_dump(self, id):
        r = requests.get("https://statsapi.web.nhl.com/api/v1/teams/{}?expand=team.roster".format(id))
        team_json = json.dumps(r.json(), indent=4)
        team_object = json.loads(team_json)
        return team_object['teams'][0]


    # this method needs to be called after parse raw NHL teams which is enforced in data driver - for now just raise exception
    # need running list of current NHL teams for getting player info by NHL team
    # the data may be old; the way that we find out is through boxscores. If player appears on new team, and its today, then update their NHL team.
    def update_NHL_teams_starters(self, week):
        print("Updating NHL teams for weekly starters.....")

        if not self.NHL_teams:
            raise NotImplementedError("need to call parse_raw_NHL_teams to get basic teams dictionary first")

        NHL_starters = self.NHL_teams
        for player in self.weeks[week]['starters']:
            # we want last known NHL team in NHL teams to be identical to that which is stored for players_NHL_team, always
            # this means whenever a players team changes, must update both.

            # since players and NHL_teams will be running lists, don't need to worry about old data corrupting the other
            # if we just ensure to update both when encounter new team.
            players_NHL_team = self.players[player]['last_known_NHL_team']
            if player not in NHL_starters[players_NHL_team]['players']:
                NHL_starters[players_NHL_team]['players'].append(player)

        self.NHL_teams = NHL_starters


    # always want to call update_NHL_teams_starters and check_for_player_info together, so just use this function to call both.
    def weekly_update_NHL_teams_and_players(self, week):
        self.update_NHL_teams_starters(week)
        self.check_for_player_info(week)
        pass


    def parse_raw_NHL_teams(self):
        teams = {}

        r = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
        teams_json = json.dumps(r.json(), indent=4)
        teams_object = json.loads(teams_json)

        for team in teams_object['teams']:
            teams[team['name']] = {'team_id': team['id'], 'players': []}

        return teams


    # need to cycle thru every player in the game, and check if they're in the weekly starters list
    def parse_player_game_stats(self, team_object, my_date):
        # go thru active skaters / goalies using list in team object
        # figure out if they are an active player for the week in question, and if so add their data to the fantasy team in question
        # also, check last known NHL team. If new, change the team.
        ######### need to decide if I should always switch, or only on todays date. I feel like always #########

        week = self.get_week(my_date)
        NHL_team = team_object['team']['name']
        roster = team_object['players']

        for player_id in roster:
            player = roster[player_id]['person']['fullName']
            if player in self.weeks[week]['starters'] and roster[player_id]['stats']:
                print(player)
                fantasy_team = self.weeks[week]['starters'][player]
                is_goalie = True if 'G' in self.players[player]['eligible_positions'] else False

                # update the correct fantasy team with the boxscore
                player_game_stats = roster[player_id]['stats']['skaterStats' if not is_goalie else 'goalieStats']
                self.weeks[week]['teams'][fantasy_team]['starters'][player][Date_Utils.date_to_string(my_date)] = player_game_stats

                # check NHL team to ensure trades get accounted for FOR ACTIVE PLAYERS ################
                if NHL_team != self.players[player]['last_known_NHL_team']:
                    print(f"{player} got traded! From the {self.players[player]['last_known_NHL_team']}s to the {NHL_team}s")

                    # make sure to set both players, and NHL teams, and REMOVE THE ENTRY FROM NHL_TEAMS
                    self.NHL_teams[self.players[player]['last_known_NHL_team']].remove(player)
                    self.NHL_teams[NHL_team].append(player)
                    self.players[player]['last_known_NHL_team'] = NHL_team



        #
        # week = self.get_week(date)
        # team = team_object['team']['name']
        # weekly_active_players = self.NHL_teams[team][week].keys()
        # roster = team_object['players']
        #
        # for player in weekly_active_players:
        #     print(player)
        #     player_id = self.players[player]['NHL_id']
        #     fantasy_team = self.players[player]['fantasy_team']
        #
        #     if 'ID{}'.format(player_id) not in roster or player_id in team_object['scratches']:
        #         continue
        #     is_goalie = True if 'G' in self.players[player]['eligible_positions'] else False
        #     player_game_stats = roster['ID{}'.format(player_id)]['stats']['skaterStats' if not is_goalie else 'goalieStats']
        #
        #     self.weeks[week][fantasy_team]['starters'][player][Date_Utils.date_to_string(date)] = player_game_stats
        #     pass


    def parse_raw_boxscore(self, game_id, date):
        game_url = self.NHL_base_url + "/game/{}/boxscore".format(game_id)
        r = requests.get(game_url)
        game_json = json.dumps(r.json(), indent=4)
        game_object = json.loads(game_json)

        away_object = game_object['teams']['away']
        home_object = game_object['teams']['home']

        self.parse_player_game_stats(away_object, date)
        self.parse_player_game_stats(home_object, date)

        pass


    def parse_raw_daily_schedule(self, date):
        schedule_url = self.NHL_base_url + "/schedule"
        schedule_url += "?date={}".format(Date_Utils.date_to_string(date))
        r = requests.get(schedule_url)
        schedule_json = json.dumps(r.json(), indent=4)
        schedule_object = json.loads(schedule_json)

        if schedule_object['totalGames'] == 0:
            return
        games_list = schedule_object['dates'][0]['games']
        for game_object in games_list:
            if game_object['gameType'] != 'R':
                continue
            game_id = game_object['gamePk']
            self.parse_raw_boxscore(game_id, date)