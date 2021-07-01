import csv
import logging
import os
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# tokens
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_user_token = os.environ["SLACK_USER_TOKEN"]

# constants
MOHIT = "U014S8CENTG"
OFFICERS  = "G01BT3PSF5H"
STUDENTS =  "C014T2194NA"
MEMBERS = "G014T21HH62"
BOT_USERNAME = "mohit" # username that message is sent as
BOT_PROFILE_PIC = "https://ca.slack-edge.com/T014Y6R3WLQ-U014S8CENTG-279666efd5ea-192" # link to profile pic in Slack

# - sends through Slackbot but uses username and icon_url set in the function
# - channel parameter can be channel or user ID (find this using conversations_list or users_info)
def send_message_to_individual(user_or_channel_id, name, message):
    client.chat_postMessage(
        channel=user_or_channel_id,
        text=f"Hi {name}! {message}",
        username=BOT_USERNAME, 
        icon_url=BOT_PROFILE_PIC 
    )


# send a message to everyone in a channel
def send_message_to_everyone_in_channel(channel_id, message):
    members = client.conversations_members(channel=channel_id, limit=400)
    count = 0
    for member in members["members"]:
        user_info = client.users_info(user=member)
        # parse first name
        if count > 200:
            name = user_info['user']['real_name'] if len(user_info['user']['real_name'].split(' ')) == 0 else user_info['user']['real_name'].split(' ')[0]
            send_message_to_individual(member, name, message)
            print(name)
        count += 1
            
    print(count)


# get channel ids
# - to get private channel id, you MUST first add the bot to the channel
def get_channel_ids():
    response = client.conversations_list(types="public_channel, private_channel")
    for channel in response['channels']:
        print(channel['name'] + ", " + channel['id'])


# adds specified user to specified channel
def add_user_to_channel(channel_id, user):
    client.conversations_invite(channel=channel_id, users=user)


# gets the user id for a person given their name
def find_user_id_using_name(name):
    students = client.conversations_members(channel=STUDENTS)
    for student in students["members"]:
        user_info = client.users_info(user=student)
        if user_info['user']['profile']['real_name'] == name:
            return student

# get names and email for members in channel
# CURRENTLY GETS MANY DUPLICATES ¯\_(ツ)_/¯
def get_info_of_members_in_channel(channel_id):
    names = []
    emails = []
    members = client.conversations_members(channel=channel_id)
    while 1:
        for member in members["members"]:
            user_info = client.users_info(user=member)
            names.append(user_info['user']['profile']['real_name'])
            emails.append(user_info['user']['profile']['email'])
        # responses are paginated, so if "next_cursor" field exists, query again
        if "next_cursor" in members["response_metadata"]:
            members = client.conversations_members(channel=channel_id, cursor=response["response_metadata"]["next_cursor"])
        else:
            break

    # dump list to excel
    with open("emails.csv", 'w', newline='') as myfile:
         print(len(emails))
         wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
         wr.writerow(names)
         wr.writerow(emails)

# input: master sheet with full name column added
# messages everyone in sheet that satisfies condition
def message_all_names_in_csv(message):
    targets = pd.read_csv('members.csv')
    first_names = list(targets['First Name'])
    last_names = list(targets['Last Name'])
    names = list(targets['Full Name'])
    emails = list(targets['Email'])
    tech_core = list(targets['Primary Tech Core'])
    count = 0

    students = client.conversations_members(channel=MEMBERS, limit=200)
    for student in students["members"]:
        user_info = client.users_info(user=student)
        if user_info['user']['profile']['real_name'] in names or user_info['user']['profile']['display_name'] in names or user_info['user']['profile']['email'] in emails:
            name = user_info['user']['real_name'] if len(user_info['user']['real_name'].split(' ')) == 0 else user_info['user']['real_name'].split(' ')[0]
            send_message_to_individual(student, name, message)
            print(name)
            count += 1
            
    print(count)


if __name__ == "__main__":
    client = WebClient(token=slack_bot_token)
    try:
        # select function here 
        message = "IEEE is hosting a Facebook SWE and UT ECE alum at our GM tonight at 7 pm to discuss fairness and responsbility in AI! Give yourself a study break and join us! Might even win some free cookies :cookie: See ya there! :blob_excited: https://utexas.zoom.us/j/96017332108"
        send_message_to_everyone_in_channel(STUDENTS, message)

    except SlackApiError as e:
        print(e.response)
        assert e.response["error"]