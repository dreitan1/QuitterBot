import discord

from discord.ext import commands
from discord.utils import get

from vars import bot_key

import asyncio
import threading

registry_lock = threading.Lock()
registry = "registry.txt"

# Track users playing together and individual games
last_games = {}
games_by_time = {}

# Track scheduled role assignments
scheduled_tasks = {}

log_channel = "bot-testing"

# Delay for 2 hours
delay = 1 # 7200

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="&", intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="&help"))

async def add_role_after_delay(cxt, user, pref, num, delay):
    try:
        await asyncio.sleep(delay)
        if num == 0:
            role = discord.utils.get(user.guild.roles, name=f"{pref}")
        else:
            # prev_role = f"{pref} x{num - 1}" if num != "1" else None
            # if prev_role:
            #     prev_role = discord.utils.get(user.guild.roles, name=prev_role)
            #     if prev_role in user.roles:
            #         await user.remove_roles(prev_role)
            role = discord.utils.get(user.guild.roles, name=f"{pref} x{num}")
        if role:
            await user.add_roles(role)
        else:
            cxt.guild.create_role(name=role)
            await user.add_roles(role)
        
        await discord.utils.get(cxt.guild.channels, name=log_channel).send(f"Assigned role {role.name} to {user.name}")
    except asyncio.CancelledError:
        pass

@client.event
async def on_message(msg):
    # If an update was sent to the match_history channel, update tags appropriately
    channel = "" if msg.channel is None else msg.channel.name
    for _ in range(1):
        if channel == "match-history" and msg.author.bot:
            name = msg.author.name
            with open(registry, 'r') as f:
                contents = f.read()
                if name not in contents:
                    break
                else:
                    contents = contents.split('\n')
                    user = [line for line in contents if name in line][0].split(',')[1]
            
            timestamp = msg.created_at.replace(second=0, microsecond=0)
            duration = msg.embeds[0].to_dict()['author']['name'][1:msg.embeds[0].to_dict()['author']['name'].find("•")-1]

            discord_user = msg.guild.get_member_named(user)
            if discord_user is None:
                break

            games_by_time.setdefault((timestamp, duration), []).append(discord_user.id)

            prev = last_games.get(discord_user.id, {})
            task = scheduled_tasks.pop(discord_user.id, None)
            if task:
                task.cancel()

            print(f"Updating for {name}")

            print(f"Embeds: {msg.embeds}")
            print(f"desc: {msg.embeds[0].description}")
            print(f"footer: {msg.embeds[0].footer}")
            print(f"fields: {msg.embeds[0].fields}")
            print(f"title: {msg.embeds[0].title}")
            print(f"dict: {msg.embeds[0].to_dict()}")
            print(f"Embed string: {str(msg.embeds[0])}")

            win_check = msg.embeds[0].description

            # Victory
            if ":2_:" in win_check:
                streak = prev.get("streak", 0) + 1 if prev.get("result", "") == "Victory" else 1
                last_games[discord_user.id] = {"result": "Victory", "streak": streak, "time": (timestamp, duration)}
                if streak == 2 and (timestamp - prev.get("time", (0, 0))[0]).total_second() <= delay:
                    # Increment winner tag, remove previous winner tag and assign incremented one
                    if len(games_by_time.get((timestamp, duration), [])) > 1:
                        if len(games_by_time.get((timestamp, duration), [])) == 2:
                            num = 0
                            for role in discord_user.roles:
                                if role.name.startswith("winner x") and int(role.name.split("x")[1]) + 1 > num:
                                    try:
                                        num = int(role.name.split("x")[1]) + 1
                                    except:
                                        pass
                                elif role.name == "winner":
                                    num = 2
                            task = asyncio.create_task(add_role_after_delay(msg, discord_user, "winner", num, delay))
                            scheduled_tasks[discord_user.id] = task
                            previous_user = games_by_time.get((timestamp, duration), [])[0]
                            num = 0
                            for role in previous_user.roles:
                                if role.name.startswith("winner x") and int(role.name.split("x")[1]) + 1 > num:
                                    try:
                                        num = int(role.name.split("x")[1]) + 1
                                    except:
                                        pass
                                elif role.name == "winner":
                                    num = 2
                            task = asyncio.create_task(add_role_after_delay(msg, previous_user, "winner", num, delay))
                            scheduled_tasks[previous_user.id] = task
                        else:
                            num = 0
                            for role in discord_user.roles:
                                if role.name.startswith("winner x") and int(role.name.split("x")[1]) + 1 > num:
                                    try:
                                        num = int(role.name.split("x")[1]) + 1
                                    except:
                                        pass
                                elif role.name == "winner":
                                    num = 2
                            task = asyncio.create_task(add_role_after_delay(msg, discord_user, "winner", num, delay))
                            scheduled_tasks[discord_user.id] = task
            # Defeat
            elif ":d_2:" in win_check:
                last_games[discord_user.id] = {"result": "Defeat", "streak": 0, "time": (timestamp, duration)}
                # Increment quitter tag, remove previous quitter tag and assign incremented one
                if len(games_by_time.get((timestamp, duration), [])) > 1:
                    if len(games_by_time.get((timestamp, duration), [])) == 2:
                        num = 0
                        for role in discord_user.roles:
                            if role.name.startswith("quitter x") and int(role.name.split("x")[1]) + 1 > num:
                                try:
                                    num = int(role.name.split("x")[1]) + 1
                                except:
                                    pass
                            elif role.name == "quitter":
                                num = 2
                        task = asyncio.create_task(add_role_after_delay(msg, discord_user, "quitter", num, delay))
                        scheduled_tasks[discord_user.id] = task
                        previous_user = games_by_time.get((timestamp, duration), [])[0]
                        num = 0
                        for role in previous_user.roles:
                            if role.name.startswith("quitter x") and int(role.name.split("x")[1]) + 1 > num:
                                try:
                                    num = int(role.name.split("x")[1]) + 1
                                except:
                                    pass
                            elif role.name == "quitter":
                                num = 2
                        task = asyncio.create_task(add_role_after_delay(msg, previous_user, "quitter", num, delay))
                        scheduled_tasks[previous_user.id] = task
                    else:
                        num = 0
                        for role in discord_user.roles:
                            if role.name.startswith("quitter x") and int(role.name.split("x")[1]) + 1 > num:
                                try:
                                    num = int(role.name.split("x")[1]) + 1
                                except:
                                    pass
                            elif role.name == "quitter":
                                num = 2
                        task = asyncio.create_task(add_role_after_delay(msg, discord_user, "quitter", num, delay))
                        scheduled_tasks[discord_user.id] = task

    await client.process_commands(msg)

client.remove_command('help')
@commands.command(name='help')
async def help(cxt):
    if cxt.message.author == client.user:
        return
    print(cxt.channel.name)
    print("Helping")
    await cxt.message.channel.send("Hi there! I'm LoserBot. I'm here to make sure all League of Legenders are properly dealt with.\n"+
                                   'Ending on a loss grants stacking "quitter" tags and ending on two wins grants stacking "winner" tags. Feel free to exchange 3 winner tags to remove a quitter tag!\n\n'+
                                   "&register [NAME]#[TAG] [DISCORD USER]: links a league account with a discord user\n"+
                                   "&unregister [NAME]#[TAG]: unlink league account\n"+
                                   "&exchange: lose a quitter tag in exchange for 3 winner tags, if available\n"+
                                   "&leaderboard: displays the top quitters/winners")

@commands.command(name='test')
async def test(cxt):
    task = asyncio.create_task(add_role_after_delay(cxt, cxt.guild.get_member_named('YelloProngs'), "quitter", 3, delay))

@commands.command(name='register')
async def register(cxt):
    if len(cxt.message.content.split()) < 2:
        await cxt.message.channel.send("Usage: &register [NAME]#[TAG] [DISCORD USER]")
        return
    
    args = cxt.message.content.split()[1:]

    # Find the argument that contains the '#'
    name_idx = next((i for i, arg in enumerate(args) if "#" in arg), None)
    if name_idx is None:
        await cxt.message.channel.send("Usage: &register [NAME]#[TAG] [DISCORD USER]")
        return

    name = " ".join(args[:name_idx + 1])
    user = args[name_idx + 1] if len(args) > name_idx + 1 else cxt.message.author.name

    if ',' in name or ',' in user:
        await cxt.message.channel.send("Commas are not allowed in names or usernames")
        return

    if "#" not in name or len(name.split("#")) != 2:
        await cxt.message.channel.send("Usage: &register [NAME]#[TAG] [DISCORD USER]")
        return
    
    if cxt.guild.get_member_named(user) is None:
        await cxt.message.channel.send("User " + user + " not found")
        return

    with registry_lock:
        with open(registry, 'r') as f:
            contents = f.read()
            if name in contents:
                await cxt.message.channel.send(name + " is already registered")
                return
        with open(registry, 'a') as f:
            f.write(name + "," + user + '\n')
    
    await cxt.message.channel.send("Registered " + user + " as " + name)
    return

@commands.command(name='unregister')
async def unregister(cxt):
    if len(cxt.message.content.split()) != 2:
        await cxt.message.channel.send("Usage: &unregister [NAME]#[TAG]")
        return

    name = cxt.message.content.split()[1]

    if "#" not in name or len(name.split("#")) != 2:
        await cxt.message.channel.send("Usage: &unregister [NAME]#[TAG]")
        return

    with registry_lock:
        with open(registry, 'r') as f:
            contents = f.read()
            if name not in contents:
                await cxt.message.channel.send(name + " is not registered")
                return
            contents = contents.split('\n')
        with open(registry, 'w') as f:
            contents = '\n'.join([line for line in contents if name not in line])
            f.write(contents)
    
    await cxt.message.channel.send("Unregistered " + name)
    return

@commands.command(name="exchange")
async def exchange(cxt):
    await cxt.message.channel.send("TODO")

@commands.command(name="leaderboard")
async def leaderboard(cxt):
    if cxt.message.author == client.user:
        return
    
    mode = "losers"

    if len(cxt.message.content.split()) == 2:
        if cxt.message.content.split()[1] in ["losers", "winners"]:
            mode = cxt.message.content.split()[1]

    leaderboard = []

    with open(registry, 'r') as f:
        contents = f.read().split('\n')
        pairs = [line.split(',') for line in contents if line != '']
    
    for name, user in pairs:
        discord_user = cxt.guild.get_member_named(user)
        if discord_user is None:
            continue
        leaderboard.append([0, 0, user, name])
        quits = 0
        wins = 0
        for role in discord_user.roles:
            if role.name == "quitter" and quits == 0:
                quits = 1
            elif role.name.startswith("quitter x"):
                try:
                    num = int(role.name.split("x")[1])
                    if num > quits:
                        quits = num
                except:
                    pass
            elif role.name == "winner" and wins == 0:
                wins = 1
            elif role.name.startswith("winner x"):
                try:
                    num = int(role.name.split("x")[1])
                    if num > wins:
                        wins = num
                except:
                    pass
        leaderboard[-1][0] = quits
        leaderboard[-1][1] = wins
    
    if leaderboard == []:
        await cxt.message.channel.send("No registered users found")
        return
    
    if mode == "losers":
        leaderboard.sort(key=lambda x: (-x[0], x[2].lower()))
    else:
        leaderboard.sort(key=lambda x: (-x[1], x[2].lower()))

    msg = f"Top {mode}:\n"
    for i in range(min(10, len(leaderboard))):
        entry = leaderboard[i]
        msg += f"{i + 1}. {entry[3]} ({entry[2]}) - {entry[0]} quitter{'s' if entry[0] != 1 else ''}, {entry[1]} winner{'s' if entry[1] != 1 else ''}\n"

    await cxt.message.channel.send(msg)
    return


client.add_command(help)
client.add_command(register)
client.add_command(unregister)
client.add_command(exchange)
client.add_command(leaderboard)
# client.add_command(test)

client.run(bot_key)
