import pandas
from yahoo_oauth import OAuth2
import json

class Yahoo_Data():
    def __init__(self, league_url):
        self.oauth = self.get_oauth_session("http://fantasysports.yahooapis.com/")
        self.league = self.get_league_data(league_url)
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
        print(league_json)

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
        print(teams_object)

        # narrowing in on the relevant content
        teams_object = teams_object['fantasy_content']['leagues']['0']['league'][1]['teams']
        print(teams_object)

        teams_list = []
        # get this bad boy
        for i in range(0,12):
            teams_list.append(teams_object[str(i)]['team'][0][2]['name'])

        return teams_list

    # return players in the league
    def get_league_players(self, league_url):
        response = self.oauth.session.get(league_url + "/players", params={'format': 'json'})
        players_json = json.dumps(response.json(), indent=4)
        print(players_json)
        players_object = json.loads(players_json)
        print(players_object)

    # return the players that on each team, storing them as sublists for each team in Yahoo_Data teams attribute
    def get_team_players(self, league_url):

        # first get the league's players and find out what team they are on
        players = self.get_league_players(league_url)


if __name__=="__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    print("****************************LEAGUE*****************************")
    no_rest_for_fleury = Yahoo_Data(league_url)
    #print(no_rest_for_fleury.league)

    print("** ** ** ** ** ** ** ** ** ** ** ** ** ** TEAMS ** ** ** ** ** ** ** ** ** ** ** ** ** ** * ")
    no_rest_for_fleury.teams = no_rest_for_fleury.get_league_teams(league_url)

    no_rest_for_fleury.get_team_players(league_url)

    # ### testing ###
    #
    # response
