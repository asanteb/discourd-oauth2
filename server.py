import os
from flask import Flask, g, session, redirect, request, url_for, jsonify, make_response
from requests_oauthlib import OAuth2Session
from flask_cors import CORS, cross_origin
import jwt


OAUTH2_CLIENT_ID = '339880437600223242'
OAUTH2_CLIENT_SECRET = 'ORZZoBABsEDkRjTG1BDQ6kT4H-hUBG6s'
OAUTH2_REDIRECT_URI = 'http://localhost:3001/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__, static_url_path='')
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/home')
def home():
    return app.send_static_file('index.html')

@app.route('/login')
def login():
    scope = request.args.get(
        'scope',
        'identify email connections guilds guilds.join')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    redir = redirect(url_for('.home'))
    res = make_response(redir)
    res.set_cookie('logged', 'True')
    return res


@app.route('/userinfo')
def info():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    connections = discord.get(API_BASE_URL + '/users/@me/connections').json()
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    return jsonify(user=user, guilds=guilds, connections=connections)


if __name__ == '__main__':
    app.run(port=3001)