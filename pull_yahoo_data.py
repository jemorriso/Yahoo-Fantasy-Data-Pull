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
        response = self.oauth.session.get(url, params={'format': 'json'})

        print(json.dumps(response.json(), indent=4))
       # print(r)
        # pulls only the league info. Look at the JSON output and see how its nested 4x
        data = pandas.io.json.json_normalize(response.json(), [['fantasy_content', 'leagues', '0', 'league']])
        self.league = data.T

    def get_league_teams(self, league_url):
        response = self.oauth.session.get(league_url + "/teams", params={'format': 'json'})
        print(json.dumps(response.json(), indent=4))

if __name__=="__main__":
    league_url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
    no_rest_for_fleury = Yahoo_Data(league_url)
    no_rest_for_fleury.get_league_teams(league_url)


