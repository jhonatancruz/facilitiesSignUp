from __future__ import print_function
from flask import Flask, render_template, session, redirect, request, url_for
from googleapiclient.discovery import build
import google_auth_oauthlib.flow, google.oauth2.credentials, oauth2client
import requests
import psycopg2
import os
from apiclient.discovery import build
import googleapiclient.discovery
from httplib2 import Http
from oauth2client import file, client, tools
import datetime
import flask

app=flask.Flask(__name__)
app.secret_key = 'Random value' #TODO: Replace this secret key with an actual secure secret key.

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['profile', 'email', 'https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'



def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    return render_template("landingStudent.html", userinfo=userinfo)

@app.route('/updateEvent',methods=["GET", "POST"])
def updateEvent():
    if request.method== "POST":
        #calendarid inputed through the modal
        modalVal= request.form["modalVal"]

        if 'credentials' not in flask.session:
            return redirect(url_for('dashboard'))
        try:
            # Load credentials from the session:
            credentials = google.oauth2.credentials.Credentials(**session['credentials'])

            # Build the service object for the Google OAuth v2 API:
            global oauth
            oauth = build('oauth2', 'v2', credentials=credentials)
            # Call methods on the service object to return a response with the user's info:
            userinfo = oauth.userinfo().get().execute()
            print(userinfo)
        except google.auth.exceptions.RefreshError:
            # Credentials are stale
            return redirect(url_for('dashboard'))

        #builds credentials necessary to have access to make edit on the calendar
        credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
        service = googleapiclient.discovery.build(
          API_SERVICE_NAME, API_VERSION, credentials=credentials)

        # First retrieve the event from the API
        event = service.events().get(calendarId='drew.edu_f72q9q390fr76cj235bml2220c@group.calendar.google.com', eventId=modalVal).execute()

        #adds the user signed in as an attendee
        someoneElse={'email': userinfo['email'],'responseStatus': 'needsAction'}
        otherList= event["attendees"]
        otherList.append(someoneElse)
        event["attendees"]= otherList

        #updates the google event
        updated_event = service.events().update(calendarId='drew.edu_f72q9q390fr76cj235bml2220c@group.calendar.google.com', eventId=modalVal, body=event).execute()

        # Save credentials back to session in case access token was refreshed.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        flask.session['credentials'] = credentials_to_dict(credentials)

        return render_template("successSignUp.html", userinfo=userinfo)



# @app.route('/data')
# def return_data():
#     start_date = request.args.get('start', '')
#     end_date = request.args.get('end', '')
#     # You'd normally use the variables above to limit the data returned
#     # you don't want to return ALL events like in this code
#     # but since no db or any real storage is implemented I'm just
#     # returning data from a text file that contains json elements
#
#     with open("/Users/jhonatancruz/Desktop/Github/facilitiesApps/workerScheduling/events.json", "r") as input_data:
#         # you should use something else here than just plaintext
#         # check out jsonfiy method or the built in json module
#         # http://flask.pocoo.org/docs/0.10/api/#module-flask.json
#         # print(input.data.read())
#         return input_data.read()



# Process OAuth authorization
@app.route('/identity/login')
def login():
    global userinfo
    if 'credentials' not in session:
        # No user session is active
        return redirect(url_for('authorize'))
    try:
        # Load credentials from the session:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])

        # Build the service object for the Google OAuth v2 API:
        global oauth
        oauth = build('oauth2', 'v2', credentials=credentials)
        # Call methods on the service object to return a response with the user's info:
        userinfo = oauth.userinfo().get().execute()
        print(userinfo)
    except google.auth.exceptions.RefreshError:
        # Credentials are stale
        return redirect(url_for('authorize'))

    # Verify that the user signed in with a 'drew.ed' email address:
    if 'hd' in userinfo: validDomain = userinfo['hd'] == 'drew.edu'
    else:                validDomain = False
    if not validDomain:
        return redirect(url_for('domainInvalid'))


    username = userinfo['email'][:userinfo['email'].index('@')]

    print(username)

    return redirect(url_for("dashboard"))

@app.route('/identity/logout')
def logout():
    if 'credentials' in session:
        # Load the credentials from the session:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
        # Request the auth server to revoke the specified credentials:
        requests.post('https://accounts.google.com/o/oauth2/revoke',
            params={'token': credentials.token},
            headers = {'content-type': 'application/x-www-form-urlencoded'})
        # Delete the credentials from the session cookie:
        del session['credentials']

    if 'doNext' in request.args and request.args['doNext'] == 'login':
        return redirect(url_for('login'))
    else:
        return render_template('logoutSuccess.html')



# Authorize using OAuth
@app.route('/identity/login/authorize')
def authorize():
    # Construct the Flow object:
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    'client_secret.json',
    scopes = ['profile', 'email', 'https://www.googleapis.com/auth/calendar'])

    # Set the Redirect URI:
    flow.redirect_uri = url_for('oauth2callback', _external = True)

    # Generate URL for request to Google's OAuth 2.0 server:
    authorization_url, state = flow.authorization_url(
        # Enable offline access so as to be able to refresh an access token withou re-prompting the user for permission
        access_type = 'offline',
        # Enable incremental authorization
        include_granted_scopes = 'true',
        # Specify the Google Apps domain so that the user can only login using a 'drew.edu' email address.
        # NOTE: This can be overridden by the user by modifying the request URL in the browser, which is why the login() view  double-checks the domain of the logged-in user's email to ensure it's a 'drew.edu' email address.
        hd = 'drew.edu'
        )

    # Store the state so the callback can verify the auth server response:
    session['state'] = state

    return redirect(authorization_url)

# Process the authorization callback
@app.route('/identity/login/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can verified in the authorization server response:
    state = session['state']

    # Reconstruct the flow object:
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    'client_secret.json',
    scopes = ['profile', 'email','https://www.googleapis.com/auth/calendar' ],
    state = state)
    flow.redirect_uri = url_for('oauth2callback', _external = True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens:
    authorization_response = request.url.strip()
    flow.fetch_token(authorization_response = authorization_response)

    # Store credentials in the session:
    session['credentials'] = credentials_to_dict(flow.credentials)

    return redirect(url_for('login'))

# Display invalid-sign-in page and prompt for re-login:
@app.route('/identity/domainInvalid')
def domainInvalid():
    return render_template('domainInvalid.html')


# HELPER FUNCTIONS
def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

if __name__== "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 8080, debug=True)
