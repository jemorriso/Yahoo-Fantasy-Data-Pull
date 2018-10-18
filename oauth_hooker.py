from yahoo_oauth import OAuth2
import logging

oauth_logger = logging.getLogger('yahoo_oauth')
oauth_logger.disabled = True
oauth = OAuth2(None, None, from_file='oauth_creds.json', base_url="http://fantasysports.yahooapis.com/")

if not oauth.token_is_valid():
    oauth.refresh_access_token()
print(oauth)

url = 'https://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=nhl.l.8681'
response = oauth.session.get(url, params={'format': 'json'})

print(response.json())