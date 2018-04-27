"""
Shows basic usage of the Google Calendar API. Creates a Google Calendar API
service object and outputs a list of the next 10 events on the user's calendar.
"""
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime

# Setup the Calendar API
SCOPES = 'https://www.googleapis.com/auth/calendar'
# https://www.googleapis.com/calendar/v3/calendars/{CALENDAR ID}/events/dbqcfrdvkm40tnuvbk46mv1ktg?key={YOUR_API_KEY}
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))

# Call the Calendar API
# now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
# print('Getting the upcoming 10 events')
# events_result = service.events().list(calendarId='drew.edu_f72q9q390fr76cj235bml2220c@group.calendar.google.com', timeMin=now,
#                                       maxResults=10, singleEvents=True,
#                                       orderBy='startTime').execute()
# events = events_result.get('items', [])
#
# if not events:
#     print('No upcoming events found.')
# for event in events:
#     start = event['start'].get('dateTime', event['start'].get('date'))
#     print(start, event['summary'])

# First retrieve the event from the API.
event = service.events().get(calendarId='drew.edu_f72q9q390fr76cj235bml2220c@group.calendar.google.com', eventId='7mhqobed8ef99dpgp74bl57njn').execute()
#
# event['attendees'] = 'jcruz3@drew.edu'
event["summary"]= 'something else'
print(event,event['summary'],event["attendees"], event['id'])

# updated_event = service.events().update(calendarId='drew.edu_f72q9q390fr76cj235bml2220c@group.calendar.google.com', eventId='7mhqobed8ef99dpgp74bl57njn', body=event).execute()


print("success?")
# Print the updated date.
# print (updated_event['updated'])

# page_token = None
# while True:
#   calendar_list = service.calendarList().list(pageToken=page_token).execute()
#   for calendar_list_entry in calendar_list['items']:
#     print (calendar_list_entry['summary'])
#   page_token = calendar_list.get('nextPageToken')
#   if not page_token:
#     break
