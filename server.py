from __future__ import print_function
import os
import pickle
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from oauth2client.service_account import ServiceAccountCredentials
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

app = Flask(__name__)

###################### SLACK ###############################################
STUDENTS = "C014T2194NA"
MEMBERS = "G014T21HH62"
slack_bot_token = "xoxb-1168229132704-1647352279894-2RIlJK5etEqZnfbjaOQsdzMP"
signing_secret = "a80f76ee29ded6a1c9af3473b818ce7f"
client = WebClient(token=slack_bot_token)
signature_verifier = SignatureVerifier(signing_secret=signing_secret)

##################### SHEETS ###############################################
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
# The ID and range of a sample spreadsheet.
MASTER_SHEET_ID = '1huIVb12OgCsIluizLQlD7lpA5_73J6V-XVi3WyuALjo'
RANGE = 'Attendance and Spark Points!A:B' # https://developers.google.com/sheets/api/guides/concepts

# unfinished
@app.route('/spark_points', methods=['POST'])
def spark_points():
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    service = build('sheets', 'v4', credentials=creds)
     # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=MASTER_SHEET_ID,
                                range=RANGE).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
    else:
        name = request.form.get('text')
        client = WebClient(token=slack_bot_token)
        students = client.conversations_members(channel=STUDENTS)
        for student in students["members"]:
            user_info = client.users_info(user=student)
            if user_info['user']['profile']['real_name'] == name:
                id = student
        for row in values:
            if row[0] == name:
                points = row[1]
        client.chat_postMessage(channel=id, text=f"Hi {name.split()[0]}! You have {points} spark points!")
        return jsonify(
            response_type='in_channel',
            text='done',
        )

# add person to members channel
@app.route('/add_to_members', methods=['POST'])
def add_to_members():
    # verify request is from slack using signing secret
    if not signature_verifier.is_valid(
        body=request.get_data(),
        timestamp=request.headers.get("X-Slack-Request-Timestamp"),
        signature=request.headers.get("X-Slack-Signature")):
        return make_response("invalid request", 403)

    # get name of member
    name = request.form.get('text')
    print(name)

    # try to find user in #students channel and get their user ID
    students = client.conversations_members(channel=STUDENTS)
    id = None
    for student in students["members"]:
        user_info = client.users_info(user=student)
        if user_info['user']['profile']['real_name'] == name:
            id = student
            break

    # if user id was found, add them to members channel
    if id is not None:
        try:
            client.conversations_invite(channel=MEMBERS, users=id)
        except SlackApiError as e:
            assert e.response["error"]

    return jsonify(
        response_type='in_channel',
        text='done',
    )
    