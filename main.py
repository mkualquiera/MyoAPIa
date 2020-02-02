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

@tasks.loop(seconds=1.2)
async def calculate_metrics():
    if not message_queue.empty():
        message_to_eval = message_queue.get()
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
                database[attribute][message_to_eval[0]]["accumulated"] = 0
                database[attribute][message_to_eval[0]]["count"] = 0
            database[attribute][message_to_eval[0]]["accumulated"] += data['summaryScore']['value']
            database[attribute][message_to_eval[0]]["count"] += 1
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
                score = data["accumulated"] / data["count"]
                ranking.append((guildMember.nick,score))
    sorted(ranking)
    for ranker in ranking:
        to_send += "{:.3f}".format(ranker[1]) + " | " + ranker[0] + "\n"
    to_send += "```"
    await channel.send(content=to_send)

@tasks.loop(seconds=3600)
async def random_ranking_loop():
    loop.create_task(random_ranking())

async def random_ranking():
    keys = list(database.keys())
    if len(keys) > 0:
        index = randint(0, len(keys))
        loop.create_task(display_attribute(keys[index]))

@client.event
async def on_ready():
    calculate_metrics.start()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    bits = message.content.split(" ")
    if len(bits) == 1:
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
    print(message_object)


client.run(token)
