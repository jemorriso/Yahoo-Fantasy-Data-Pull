import pandas
from yahoo_oauth import OAuth2
import json

class Yahoo_Data():
    def __init__(self, league_url):
        self.oauth = self.get_oauth_session("http://fantasysports.yahooapis.com/")
        self.league = {'league info': self.get_league_data(league_url)}
        self.teams = None

    # utilizing yahoo-oauth api
    def get_oauth_session(self, url):
        oauth = OAuth2(None, None, from_file='oauth_creds.json', base_url=url)

        if not oauth.token_is_valid():
            oauth.refresh_access_token()

        return oauth

    def get_league_data(self, url):
        # returns Oauth "response" object, which I guess must be converted to json.
        # above is WRONG. rauth utilizes python Requests module, so its a python Requests response object that is being returned.

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

    def get_league_teams(self, league_url):
        response = self.oauth.session.get(league_url + "/teams", params={'format': 'json'})

        # decodes the response into json format
        teams_json = json.dumps(response.json(), indent=4)

        teams_object = json.loads(teams_json)
        #print(teams_object)

        # narrowing in on the relevant content
        teams_object = teams_object['fantasy_content']['leagues']['0']['league'][1]['teams']
        # print(teams_object)

        teams_dict = {}
        # get this bad boy: create nested dict where key is team name
        for i in range(0,12):
            team_name = teams_object[str(i)]['team'][0][2]['name']
            team_key = teams_object[str(i)]['team'][0][0]['team_key']
            teams_dict[team_name] = {'yahoo key': team_key}
            # teams_dict[team_name]['key'] = team_key
        return teams_dict

    # # return players in the league
    # def get_league_players(self, league_url):
    #     response = self.oauth.session.get(league_url + "/players", params={'format': 'json'})
    #     players_json = json.dumps(response.json(), indent=4)
    #     print(players_json)
    #     players_object = json.loads(players_json)
    #     print(players_object)

    # return the players that on each team, storing them as sublists for each team in Yahoo_Data teams attribute
    def get_team_players(self, base_url):
        starting_positions = ['C', 'LW', 'RW', 'D', 'G', 'Util']

        # cycle through each team and grab their players
        for team in self.teams.keys():
            response = self.oauth.session.get(base_url + "/teams;team_keys={}/roster".format(self.teams[team]['yahoo key']),
                                                        params={'format': 'json'})
            players_json = json.dumps(response.json(), indent = 4)
            players_object = json.loads(players_json)
            #
            # #print(players_object)
            # # get to relevant info
            # print(team)
            players_object = players_object['fantasy_content']['teams']['0']['team'][1]['roster']['0']['players']

            # bench includes IR players
            players_dict = {'starters':[], 'bench':[]}
            for i in range(0,players_object['count']):
                player_info = players_object[str(i)]['player']
                if player_info[1]['selected_position'][1]['position'] in starting_positions:
                    players_dict['starters'].append(player_info[0][2]['name']['full'])
                else:
                    players_dict['bench'].append(player_info[0][2]['name']['full'])

            # add player list to team data structure for each team
            self.teams[team]['players'] = players_dict

    def get_scoring_categories(self, league_url):
        response = self.oauth.session.get(league_url + "/settings", params={'format': 'json'})

        settings_json = json.dumps(response.json(), indent=4)
        settings_object = json.loads(settings_json)
        print(settings_object)

        settings_object = settings_object['fantasy_content']['leagues']['0']['league'][1]['settings'][0]['stat_categories']['stats']
        print(settings_object)

        scoring_categories= {}

        for x in settings_object:
            abbreviation = x['stat']['display_name']
            scoring_categories[abbreviation] = x['stat']['name']

        self.league['scoring categories'] = scoring_categories

if __name__=="__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    base_url = 'https://fantasysports.yahooapis.com/fantasy/v2'

    print("****************************LEAGUE*****************************")
    no_rest_for_fleury = Yahoo_Data(league_url)
    #print(no_rest_for_fleury.league)
    no_rest_for_fleury.get_scoring_categories(league_url)

    print("** ** ** ** ** ** ** ** ** ** ** ** ** ** TEAMS ** ** ** ** ** ** ** ** ** ** ** ** ** ** * ")
    no_rest_for_fleury.teams = no_rest_for_fleury.get_league_teams(league_url)

    no_rest_for_fleury.get_team_players(base_url)

    print(no_rest_for_fleury.teams)

    # each league team format is 386.l.8681.t.n
    # where n is 1 through 12
    #
    # test1 = (json.dumps(response.json(), indent=4))
    # test2 = json.loads(test1)
    # print(json.dumps(response.json(), indent=4))
    # response

    ## TESTING ##########################
    # response = no_rest_for_fleury.oauth.session.get(base_url + "/teams;team_keys=386.l.8681.t.3/roster",
    #                                   params={'format': 'json'})
    #
    # test1 = (json.dumps(response.json(), indent=4))
    # print(test1)
    # test2 = json.loads(test1)
    # print(test2)