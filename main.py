import os
import asyncio
import threading
import discord
import json
import requests
from random import randint
from discord.ext import tasks
from dotenv import load_dotenv
import queue

client = discord.Client()
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
channel_name = os.getenv('CHANNEL')
api_key = os.getenv('API_KEY')

message_queue = queue.Queue()

database = {}

loop = asyncio.get_event_loop()

'''@tasks.loop(seconds=1.2)
async def calculate_metrics():
    if not message_queue.empty():
        message_to_eval = message_queue.get()
        if message_to_eval[1] == '':
            return
        print("evaluating message", message_to_eval)
        url = ('https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze' +
            '?key=' + api_key)
        data_dict = {
            'comment': {'text': message_to_eval[1]},
            'languages': ['en'],
            'requestedAttributes': {'TOXICITY': {}, 'INSULT': {}, 'PROFANITY': {}, 'THREAT': {}, 'SEXUALLY_EXPLICIT':{}, 'FLIRTATION':{}}
        }
        print("sent request")
        response = requests.post(url=url, data=json.dumps(data_dict))
        response_dict = json.loads(response.content)
        print("parsed response")
        #response_dict['attributeScores']['PROFANITY']['summaryScore']['value']
        for attribute, data in response_dict['attributeScores'].items():
            print("Adding to attribute", attribute)
            if not attribute in database:
                database[attribute] = {}
            if not message_to_eval[0] in database[attribute]:
                database[attribute][message_to_eval[0]] = {}
                database[attribute][message_to_eval[0]]["average"] = data['summaryScore']['value']
            else:
                database[attribute][message_to_eval[0]]["average"] = data['summaryScore']['value'] * 0.18 + database[attribute][message_to_eval[0]]["average"] * (1.0 - 0.18)
            print("done")
        print("processed attributes")
        print(database)

async def display_attribute(attribute, channel=None):
    print("displaying", attribute)
    print("channel", channel)
    if not attribute in database:
        return
    if channel == None:
        for guild in client.guilds:
            for channelInt in guild.channels:
                if channelInt.name == channel_name:
                    loop.create_task(display_attribute(attribute, channelInt))
                    return
    to_send = "Ranking by " + attribute + "\n"
    to_send += "```Score | Human being (or robot?)\n"
    ranking = []
    for databaseMember, data in database[attribute].items():
        for guildMember in channel.guild.members:
            if guildMember.mention == databaseMember:
                score = data["average"]
                ranking.append((score,guildMember.display_name))
    ranking = sorted(ranking, key=lambda x: x[0], reverse=True)
    for ranker in ranking:
        to_send += "{:.3f}".format(ranker[0]) + " | " + ranker[1] + "\n"
    to_send += "```"
    await channel.send(content=to_send)

@tasks.loop(seconds=3600)
async def random_ranking_loop():
    loop.create_task(random_ranking())

async def random_ranking():
    keys = list(database.keys())
    if len(keys) > 0:
        index = randint(0, len(keys)-1)
        loop.create_task(display_attribute(keys[index]))

@client.event
async def on_ready():
    calculate_metrics.start()
    random_ranking_loop.start()'''

def evaluate_message(message_to_eval):
    if message_to_eval == '':
        return
    print("evaluating message", message_to_eval)
    url = ('https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze' +
        '?key=' + api_key)
    data_dict = {
        'comment': {'text': message_to_eval},
        'languages': ['en'],
        'requestedAttributes': {'TOXICITY': {}, 'INSULT': {}, 'PROFANITY': {}, 'THREAT': {}, 'SEXUALLY_EXPLICIT':{}, 'FLIRTATION':{}}
    }
    print("sent request")
    response = requests.post(url=url, data=json.dumps(data_dict))
    response_dict = json.loads(response.content)
    print("parsed response")
    attributes_string = ""
    #response_dict['attributeScores']['PROFANITY']['summaryScore']['value']
    for attribute, data in response_dict['attributeScores'].items():
        attributes_string += attribute + " : " + str(response_dict['attributeScores'][attribute]['summaryScore']['value']) + "\n"
    print("done")
    return attributes_string

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    bits = message.content.split(" ")
    if len(bits) > 0:
        if bits[0].replace("!","") == client.user.mention.replace("!",""):
            actual_message = message.content[len(client.user.mention):]
            result = evaluate_message(actual_message)
            result = "Attributes for this message: ```" + result + "```"
            await message.channel.send(content=result)
            return
    '''if len(bits) == 1:
        if bits[0] == "!attributes":
            to_send = "Available attributes: ```"
            for attr in database.keys():
                to_send += attr + "\n"
            to_send += "```"
            await message.channel.send(content=to_send)
            return
        if bits[0] == "!debug_rand":
            loop.create_task(random_ranking())
            return
    if len(bits) == 2:
        if bits[0] == "!ranking":
            if bits[1] in database:
                loop.create_task(display_attribute(bits[1], message.channel))
                return
            else:
                await message.channel.send(content="That attribute does not exist.")
                return


    message_object = (message.author.mention, message.content)
    message_queue.put(message_object)
    print(message_object)'''


client.run(token)
