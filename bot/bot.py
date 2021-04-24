#====================================
#Author: Kevin "Sporti" Vigil (Discord: Sporti#0001)
#Date: 02/16/2021
#Program: UTD Minecraft Whitelisting Bot
#Description: This program will automate whitelisting for users who wish to join The University of Texas at Dallas Esports Minecraft Server
#               using commands issued in the UTD Esports Discord Server. Features include: Automatic whitelisting into the UTD Minecraft servers
#               via discord, newletter subscription, ban management, automatic newsletter recipient email formatting via command
#
#Sections (copy -> ctrl+F -> paste to jump to sections):
#   -Sqlite3 Database Functions
#   -Bot Message Embeds
#   -Admin Functions
#   -All Use Helper Functions
#   -All User Commands
#=====================================


import discord
import sqlite3
import asyncio
from asyncio import TimeoutError
from discord.ext import commands
from rcon import rcon
import re
from mojang import MojangAPI
import datetime
from mcrcon import MCRcon
import numpy as np
import os
import psycopg2
#from tenv import load_dotenv




pgURL = str(os.environ.get('DATABASE_URL'))
#print(pgURL)
#pgUser = ""
#pgdb = ""
#pgPass = ""
#pgHost = ""
#pgPort = ""

m = re.search('@(.+?)/', pgURL)
if m:
    global pgHost
    global pgPort
    strr = str(m.group(1))
    pgHost = str(strr.split(":")[0])
    pgPort = str(strr.split(":")[1])
m = re.search('//(.+?):', pgURL)
if m:
    global pgUser
    pgUser = m.group(1)

pgURL = pgURL.split("//")[1]
m = re.search(':(.+?)@', pgURL)
if m:
    global pgPass
    pgPass = str(m.group(1))


m = re.search('\/(.+?)$', pgURL)
if m:
    global pgdb
    pgdb = m.group(1)

#print("Listing all information based on test case: \npgHost: " + str(pgHost) + "\npgPort: " + str(pgPort) + "\npgUser: " + str(pgUser) + "\npgPass: " + str(pgPass) + "\npgdb: " + str(pgdb))

#Connects to the database using the sqlite3 library
#conn = sqlite3.connect('..\\DB\\mcData.db')
conn = psycopg2.connect(database = pgdb, user = pgUser, password = pgPass, host = pgHost, port = pgPort)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS serverconfig
                (server_id INT PRIMARY KEY NOT NULL UNIQUE,
                 channel_id INT NOT NULL UNIQUE,
                 preset TEXT,
                 ip TEXT,
                 port INT,
                 password TEXT);''')
cur.execute('''CREATE TABLE IF NOT EXISTS whitelist
                (user_id INT PRIMARY KEY NOT NULL UNIQUE,
                 first_name TEXT NOT NULL,
                 last_name TEXT NOT NULL,
                 uuid TEXT NOT NULL UNIQUE,
                 username TEXT NOT NULL UNIQUE,
                 email TEXT NOT NULL,
                 isBanned INT NOT NULL);''')
conn.commit()

#regex expression for email validation
regSearch = re.compile(r'^([A-Za-z0-9_]+([A-Za-z0-9!#$%&\'\*+/=?^_`{|}~-]\.?)*[A-Za-z0-9_]@(([A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]\.)+[A-Za-z]+|\[(\d{3}\.?){4}\]|(\d{3}\.?){4}))$')

#Variables for config, Change here to set up in own server
CHANNELID = 0
rconIp = ""
rconPort = 0
rconPass = ""


#============================Sqlite3 Database Functions===========================
#-----------------------writing functions-----------------------

# remove_player(user_id) Removes the user from the database.
# Returns:
#       true: user removed, false: user not found
def remove_player(user_id):
    if poll(user_id) != False:
        cur.execute("DELETE FROM whitelist WHERE user_id=?", (int(user_id),))
        conn.commit()

        return True
    else:
        return False

# edit_player(user_id, uuid, username) will edit the corresponding user's uuid and minecraft username in the database
# Returns:
#       true: player edited success, false: user not found
def edit_username(user_id, uuid, username):
    if poll(user_id) != False:
        cur.execute("UPDATE whitelist SET uuid=?, username=? WHERE user_id=?", (str(uuid), str(username), int(user_id)))
        conn.commit()

        return True
    else:
        return False

#-----------------------reading functions-----------------------

# poll(user_id) will search for the user using the primary key (user_id) and return entry
# Returns:
#       true: returns the user information, false: player not found
def poll(user_id):
    cur.execute("SELECT * FROM whitelist WHERE user_id = ?", (int(user_id),))

    a = cur.fetchone()

    if str(a) == 'None':
        return False
    else:
        return a

# uuidPoll(user_id) will poll the user using the uuid and return entry
# Returns:
#       true: returns the player if uuid exists, false: player not found
def uuidPoll(uuid):
    cur.execute("SELECT * FROM whitelist WHERE uuid=?", (str(uuid),))

    a = cur.fetchone()

    if str(a) == 'None':
        return False
    else:
        return a

#==============================Bot Message Embeds===============================


#Constants
PROMPT_C = 0xf1c40f
SUCCESS_C = 0x3CFF8F
ERROR_C = 0xFF4B4B

EMB_ICON = 'https://utdcomets.com/images/main-logo.png'
EMD_NAME = 'UT Dallas Minecraft' #change for personalization

#============================Minecraft Username (initial whitelisting) Embeds============================

# ------------------Minecraft Username Query Prompt------------------
addAccount_embed = discord.Embed(
    title='Add your acccount!',
    description='Please reply below with your in game username.',
    colour=PROMPT_C
    )

addAccount_embed.set_footer(text='Contact Sporti#0001 for support.')
addAccount_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

# ------------------info Confirmation (This is used for both query and edit functions)------------------
def infoConfirmation(first,last,mc):
    addConfirmPrompt_embed = discord.Embed(
        title=f'Is this information correct? ',
        description=f'React to this message with a 👍 if correct or 👎 if incorrect \nFirst Name: {first} \nLast Name: {last}\nUsername: {mc}',
        colour=PROMPT_C
        )

    addConfirmPrompt_embed.set_footer(text='Contact Sporti#0001 for support.')
    addConfirmPrompt_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)
    return addConfirmPrompt_embed

#============================Full Name (initial whitelisting) Embeds============================

# ------------------Full Name Query Prompt------------------
name_embed = discord.Embed(
    title='Add your acccount!',
    description='Please enter your first and last name.',
    colour=PROMPT_C
    )

name_embed.set_footer(text='Contact Sporti#0001 for support.')
name_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

# ------------------Full Name Confirmation (This is used for both query and edit functions)------------------
def nameConfirmation(mc):
    nameConfirm_embed = discord.Embed(
        title=f'Is "{mc}" correct? ',
        description=f'React to this message with a 👍 if correct or 👎 if incorrect',
        colour=PROMPT_C
        )

    nameConfirm_embed.set_footer(text='Contact Sporti#0001 for support.')
    nameConfirm_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)
    return nameConfirm_embed


#============================Subscription Embeds=============================

#--------------------------Subscribe Prompt----------------------
subPrompt_embed = discord.Embed(
    title=f'Would you like to subscribe to our newsletter to recieve updates for the server?',
    description=f'React below with 👍 to recieve updates or 👎 otherwise.',
    colour=PROMPT_C
    )

subPrompt_embed.set_footer(text='Contact Sporti#0001 for support.')
subPrompt_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#-----------------------Subscribe Email prompt----------------------------------
newsPrompt = discord.Embed(
    title='Please enter your email!',
    description='Please enter a valid email address below.',
    colour=PROMPT_C
    )

newsPrompt.set_footer(text='Contact Sporti#0001 for support.')
newsPrompt.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#--------------------------Subscribe Email Confirmation----------------------
def subConfirm(email):
    subConfirm_embed = discord.Embed(
        title=f'Is the email "{email}" correct?',
        description=f'React to this message with a 👍 if correct or 👎 if incorrect',
        colour=PROMPT_C
        )

    subConfirm_embed.set_footer(text='Contact Sporti#0001 for support.')
    subConfirm_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)
    return subConfirm_embed

#-----------------------Not Subscribed----------------------------------
notSubbed_embed = discord.Embed(
    title='You have not been subscribed.',
    description='If you wish to subscribe at any time, Please use the $subscribe command.',
    colour=PROMPT_C
    )

notSubbed_embed.set_footer(text='Contact Sporti#0001 for support.')
notSubbed_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#-----------------------Unsubscribe Confirmation----------------------------------
unsub_embed = discord.Embed(
    title=f'Are you sure?',
    description=f'React to this message with a 👍 to unsubscribe or 👎 to keep recieving updates.',
    colour=PROMPT_C
    )

unsub_embed.set_footer(text='Contact Sporti#0001 for support.')
unsub_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)


#===============================Edit Embeds=============================

# ------------------Minecraft Username Edit Prompt------------------
editMCPrompt_embed = discord.Embed(
    title='Change your linked account!',
    description='Please enter your new Minecraft Username.',
    colour=PROMPT_C
    )

editMCPrompt_embed.set_footer(text='Contact Sporti#0001 for support.')
editMCPrompt_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#-----------------Minecraft Username Edit Confirmation--------------
def usernameConfirmation(mc):
    addConfirmPrompt_embed = discord.Embed(
        title=f'Is the username {mc} correct? ',
        description=f'React to this message with a 👍 if correct or 👎 if incorrect.',
        colour=PROMPT_C
        )

    addConfirmPrompt_embed.set_footer(text='Contact Sporti#0001 for support.')
    addConfirmPrompt_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)
    return addConfirmPrompt_embed


#==============================Removal Embeds============================

# ------------------Removal Confirmation------------------
removeConfirmPrompt_embed = discord.Embed(
    title='Are you sure?',
    description='This will un-whitelist you from the UTD Minecraft Server.\nReact to this message with a 👍 if you want to leave or a 👎 if not.',
    colour=PROMPT_C
    )

removeConfirmPrompt_embed.set_footer(text='Contact Sporti#0001 for support.')
removeConfirmPrompt_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)


#=============================Completion Embeds==========================

# ------------------Whitelisting completion message------------------
addFinish_embed = discord.Embed(
    title='Welcome!',
    description=f'Thank you for joining our Minecraft community. We hope you have a great time and enjoy the server!',
    colour=SUCCESS_C
    )

addFinish_embed.set_footer(text='Contact Sporti#0001 for support.')
addFinish_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#------------------------Subscription Completion----------------------------------------
finished_embed = discord.Embed(
    title='All done!',
    description=f'Thank you for subscribing! If you wish to unsubscribe, please use the $unsub command.',
    colour=SUCCESS_C
    )

finished_embed.set_footer(text='Contact Sporti#0001 for support.')
finished_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

# ------------------Minecraft Username Edit Completion------------------
def editConfirm(mc):
    editConfirm_embed = discord.Embed(
        title='Account updated!',
        description=f'We\'ve successfully changed your linked account username to "{mc}"!',
        colour=SUCCESS_C
        )

    editConfirm_embed.set_footer(text='Contact Sporti#0001 for support.')
    editConfirm_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)
    return editConfirm_embed

# ------------------Removal Completion------------------
removeConfirm_embed = discord.Embed(
    title='Thanks for playing!',
    description=f'We\'re sad to see you go. Thank you for joining our community and we hope to see you back again soon!',
    colour=SUCCESS_C
    )

removeConfirm_embed.set_footer(text='Contact Sporti#0001 for support.')
removeConfirm_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#-----------------------Unsubscribe Completion----------------------------------
unsubComplete_embed = discord.Embed(
    title=f'All done!',
    description=f'You have been unsubscribed. If you wish to subscribe at any time, please use the $subscribe command.',
    colour=SUCCESS_C
    )

unsubComplete_embed.set_footer(text='Contact Sporti#0001 for support.')
unsubComplete_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)


#=============================Error Embeds================================

# ------------------Account not found or valid Error------------------
UserNotFound_embed = discord.Embed(
    title='Invalid account.',
    description=f'This username does not exist or is not valid with Minecraft username requirements.\nPlease visit https://help.minecraft.net/hc/en-us/articles/360034636712-Minecraft-Usernames for username requirements.',
    colour=ERROR_C
    )

UserNotFound_embed.set_footer(text='Contact Sporti#0001 for support.')
UserNotFound_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#------------------Account already in database Error------------------------
def existsEmbed(mc):
    invalid_embed = discord.Embed(
        title='Uh Oh!',
        description=f'The username "{mc}" has already been linked to another discord account.',
        colour=ERROR_C
        )

    invalid_embed.set_footer(text='Contact Sporti#0001 for support and please contact UTD Minecraft Admins to resolve issue.')
    invalid_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)
    return invalid_embed

#------------------Account already linked Error---------------------------
linked_embed = discord.Embed(
    title='Uh Oh!',
    description=f'This username has already been linked to your discord account. Please use $whitelist again to change it.',
    colour=ERROR_C
    )

linked_embed.set_footer(text='Contact Sporti#0001 for support.')
linked_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#------------------Timeout Error---------------------------
timeout_embed = discord.Embed(
    title='',
    description=f'You have Timed out.',
    colour=ERROR_C
    )

timeout_embed.set_footer(text='Contact Sporti#0001 for support.')
timeout_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)

#==============================MISC OR UNUSED========================================

#------------------Edit Info Prompt------------------
editPrompt_embed = discord.Embed(
    title='Change your linked account!',
    description='React with 🔑 to change your username and 📧 to change your email',
    colour=PROMPT_C
    )

editPrompt_embed.set_footer(text='Contact Sporti#0001 for support.')
editPrompt_embed.set_author(name=EMD_NAME, icon_url=EMB_ICON)



if __name__ == "__main__":

    #some things in the code need to be changed when moving servers. ### at the beginning will state where those changes will have to be made

    #sets the preset and creates the bot to run commands
    bot = commands.Bot(command_prefix='$')

    @bot.event
    async def on_ready():
        print("starting bot and setting config")
        #load_dotenv()
        global prefix
        global CHANNELID
        global rconIp
        global rconPort
        global rconPass

        cur.execute("SELECT * FROM serverconfig")
        a = cur.fetchone()

        if a != None:
            bot.command_prefix = str(a[2])
            CHANNELID = int(a[1])
            rconIp = str(a[3])
            rconPort = int(a[4])
            rconPass = str(a[5])
            mcr = MCRcon(str(rconIp), str(rconPass), port = int(rconPort))
            mcr.connect()
            resp = mcr.command("/help")
            print(resp)
            mcr.disconnect()
        else:
            print("please run $setup")



        print("Bot ready")


#==================================Admind Helper Functions==========================

    async def initialSetup(ctx):
        sersetup = [ctx.guild.id,0,"","",0,""]
        def check(m):
            return m.author == ctx.author and m.channel.type == discord.ChannelType.private

        while True:
            await ctx.author.send("please enter a channel id have the bot bound to or enter 0 to allow bot to be used throughout the entire server.")
            #print("passed the channel message")
            try:
                resp = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                return False
            else:
                try:
                    resp = int(resp.content)
                except ValueError:
                    await ctx.author.send("invalid channel id. please restart")
                    continue
                sersetup[1] = int(resp)
                global CHANNELID
                CHANNELID = int(resp)
                break
        while True:
            await ctx.author.send("please enter a prefix for the bot.")
            try:
                resp = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                return False
            else:
                resp = resp.content
                sersetup[2] = resp
                bot.command_prefix = str(resp)
                break
        while True:
            await ctx.author.send("please enter the rcon IP for the bot.")
            try:
                resp = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                return False
            else:
                resp = resp.content
                sersetup[3] = resp
                global rconIp
                rconIp = resp
                break
        while True:
            await ctx.author.send("please enter the rcon port for the bot.")
            try:
                resp = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                return False
            else:
                try:
                    resp = int(resp.content)
                except ValueError:
                    await ctx.author.send("not a number. please restart")
                    continue
                sersetup[4] = int(resp)
                global rconPort
                rconPort = int(resp)
                break
        while True:
            await ctx.author.send("please enter the rcon password for the bot.")
            try:
                resp = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                return False
            else:
                resp = resp.content
                sersetup[5] = resp
                global rconPass
                rconPass = resp
                break
        return sersetup

    async def menuSelect(ctx, sersetup):
        sersetup = np.asarray(sersetup)
        #print(sersetup)

        def check(m):
            return m.author == ctx.author and m.channel.type == discord.ChannelType.private

        while True:

            await ctx.author.send("choose an option from the menu to set:\n0 - Exit menu \t 1 - Channel_id\n2 - Preset \t\t\t3 - rcon IP\n4 - rcon Port \t  5 - rcon Password")
            try:
                menSel = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                return sersetup
            else:
                menSel = menSel.content
                if menSel == "0":
                    return sersetup
                elif menSel == "1":
                    await ctx.author.send("please enter a channel id to bound the bot to. to find channel id, right click desired channel and copy id (must be in developer mode to copy id)")
                    try:
                        resp = await bot.wait_for('message', check = check, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                        await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                        return sersetup
                    else:
                        try:
                            resp = int(resp.content)
                        except ValueError:
                            await ctx.author.send("invalid channel id. please restart")
                            continue
                        sersetup[1] = int(resp)
                        global CHANNELID
                        CHANNELID = int(resp)
                        await ctx.author.send("channel id set")

                elif menSel == '2':
                    await ctx.author.send("please enter a preset.")
                    try:
                        resp = await bot.wait_for('message', check = check, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                        await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                        return sersetup
                    else:
                        resp = resp.content
                        sersetup[2] = resp
                        bot.command_prefix = str(resp)
                        await ctx.author.send("preset set")

                elif menSel == "3":
                    await ctx.author.send("please enter the rcon ip")
                    try:
                        resp = await bot.wait_for('message', check = check, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                        await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                        return sersetup
                    else:
                        resp = resp.content
                        sersetup[3] = resp
                        global rconIp
                        rconIp = resp
                        await ctx.author.send("rcon ip set")

                elif menSel == "4":
                    await ctx.author.send("please enter the rcon port.")
                    try:
                        resp = await bot.wait_for('message', check = check, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                        await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                        return sersetup
                    else:
                        try:
                            resp = int(resp.content)
                        except ValueError:
                            await ctx.author.send("invalid response. please restart")
                            continue
                        sersetup[4] = int(resp)
                        global rconPort
                        rconPort = int(resp)
                        await ctx.author.send("rcon port set")

                elif menSel == "5":
                    await ctx.author.send("please enter the rcon password.")
                    try:
                        resp = await bot.wait_for('message', check = check, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Time out on setup menu select, possible changes still made.")
                        await ctx.author.send("Timed out! all changes have been saved. please restart setup to continue")
                        return sersetup
                    else:
                        resp = resp.content
                        sersetup[5] = resp
                        global rconPass
                        rconPass = resp
                        await ctx.author.send("rcon password set")

                else:
                    await ctx.author.send("invalid menu choice! please try again.")

#=============================Admin Functions=======================================

    @bot.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup(ctx):
        cur.execute("SELECT * FROM serverconfig WHERE server_id = ?", (ctx.guild.id,))
        ser = cur.fetchone()
        if ser != None:
            #print(ser)
            ser = await menuSelect(ctx, ser)
            #print(ser)
            cur.execute("UPDATE serverconfig SET channel_id = ?, preset = ?, ip = ?, port = ?, password = ? WHERE server_id = ?", (int(ser[1]), str(ser[2]), str(ser[3]), int(ser[4]), str(ser[5]), int(ser[0])))
            conn.commit()
        else:
            #print("going into initial setup")
            ser = await initialSetup(ctx)
            if ser != False:
                #print(ser)
                cur.execute("INSERT INTO serverconfig (server_id, channel_id, preset, ip, port, password) VALUES (?, ?, ?, ?, ?, ?)", (int(ser[0]), int(ser[1]), str(ser[2]), str(ser[3]), int(ser[4]), str(ser[5])))
                conn.commit()
        await ctx.author.send("Setup Complete.")


    @bot.command()
    @commands.has_permissions(administrator=True)
    async def news(ctx):
        if rconIp == "":
            await ctx.author.send("please run $setup before using any commmands")
            return False
        dategen = datetime.datetime.now()
        filename = str(dategen.strftime("%m")) + "_" + str(dategen.strftime("%d")) + "_" + str(dategen.strftime("%Y")) + ".txt" #text name generation using mm/dd/yyyy format
        f = open(str(filename),"w")
        cur.execute("SELECT * FROM whitelist")
        #f.write("This file was made on " + str(dategen) + ". copy and paste the text below into the \"to\" section.\n\n")
        writingLines = ""
        for row in cur:
            #print(row[0]) #debugging
            if row[3] != "NA":
                writingLines += str(row[3]) + "; "
        f.write(writingLines)
        f.close()
        await ctx.author.send("This file was generated on " + str(dategen) + ". Every email should be valid, however, please notify Sporti#0001 about emails that are not valid",file = discord.File(str(filename)))





#==========================All Use Helper Functions=================================

    #-------------------
    #Function: query(ctx)
    #Parameters: ctx    Context Parameter
    #Description: query(ctx) will prompt the user, using the given context parameter, for their username and will then confirm
    #               with timeouts on prompts to reduce bot load and eliminate unused instances
    #-------------------
    async def query(ctx):
        while True:
            await ctx.author.send(embed = name_embed)

            def check(m):
                return m.author == ctx.author and m.channel.type == discord.ChannelType.private

            try:
                namee = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Time out on name query, No changes to database.")
                await ctx.author.send(embed = timeout_embed)
                return False
            else:
                namee = namee.content
                stuff = namee.split()
                if len(stuff) != 2:
                    continue
                await ctx.author.send(embed = addAccount_embed)
                try:
                    mcUser = await bot.wait_for('message', check = check, timeout = 300)
                except TimeoutError:
                    print("User " + str(ctx.author) + "Timed out on username query, No changes to database")
                    await ctx.author.send(embed = timeout_embed)
                    return False
                else:
                    mcUser = mcUser.content
                    uuid = MojangAPI.get_uuid(mcUser)
                    if not uuid:
                        await ctx.author.send(embed = UserNotFound_embed)
                        continue
                    elif uuidPoll(uuid):
                        if uuidPoll(uuid)[0] == ctx.author.id:
                            await ctx.author.send(embed = linked_embed)
                            return False
                        await ctx.author.send(embed = existsEmbed(mcUser))
                        continue
                    else:
                        msgPrompt = await ctx.author.send(embed = infoConfirmation(stuff[0],stuff[1],mcUser))
                        thumbsup, thumbsdown = '👍','👎'
                        await msgPrompt.add_reaction(thumbsup)
                        await msgPrompt.add_reaction(thumbsdown)

                        def checkreact(reaction, react):
                            react = str(reaction.emoji)
                            return ((react == '👍' or react == '👎') and (reaction.message.id == msgPrompt.id))

                        await asyncio.sleep(.1)
                        try:
                            confirmation = await bot.wait_for('reaction_add', check = checkreact, timeout = 300)
                        except TimeoutError:
                            print("User " + str(ctx.author) + "Timed out on username confirmation, No changes to database")
                            await ctx.author.send(embed = timeout_embed)
                            return False
                        else:
                            if str(confirmation[0].emoji) == '👍':
                                return (stuff[0], stuff[1], uuid, mcUser)



    async def edit(ctx):
        while True:
            await ctx.author.send(embed = editMCPrompt_embed)

            def check(m):
                return m.author == ctx.author and m.channel.type == discord.ChannelType.private

            try:
                mcUser = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + "Timed out on edit query, Username remains unchanged")
                await ctx.author.send(embed = timeout_embed)
                return False
            else:
                mcUser = mcUser.content
                uuid = MojangAPI.get_uuid(mcUser)
                if not uuid:
                    await ctx.author.send(embed = UserNotFound_embed)
                    continue
                elif uuidPoll(uuid):
                    if uuidPoll(uuid)[0] == ctx.author.id:
                        await ctx.author.send(embed = linked_embed)
                        return False
                    await ctx.author.send(embed = existsEmbed(mcUser))
                    continue
                else:
                    msgPrompt = await ctx.author.send(embed = usernameConfirmation(mcUser))
                    thumbsup, thumbsdown = '👍','👎'
                    await msgPrompt.add_reaction(thumbsup)
                    await msgPrompt.add_reaction(thumbsdown)

                    def checkreact(reaction, react):
                        react = str(reaction.emoji)
                        return ((react == '👍' or react == '👎') and (reaction.message.id == msgPrompt.id))

                    await asyncio.sleep(.1)
                    try:
                        confirmation = await bot.wait_for('reaction_add', check = checkreact, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Timed out on edit confirmation, Username remains unchanged")
                        await ctx.author.send(embed = timeout_embed)
                        return False
                    else:
                        if str(confirmation[0].emoji) == '👍':
                            tempName = poll(ctx.author.id)[4]
                            #print("changing username: " + tempName)
                            cur.execute("UPDATE whitelist SET uuid = ?, username = ? WHERE user_id = ?", (str(uuid), str(mcUser), ctx.author.id))
                            conn.commit()
                            mcr = MCRcon(str(rconIp), str(rconPass), port = int(rconPort))
                            mcr.connect()
                            resp = mcr.command("whitelist remove " + tempName)
                            print(resp)
                            resp = mcr.command("whitelist add " + mcUser)
                            print(resp)
                            mcr.disconnect()
                            await ctx.author.send(embed = editConfirm(mcUser))
                            return True
        #"([\w]+([\w!#$%&'\*+/=?^_`{|}~-]\.?)*[\w]@(([\w][\w-]*[\w]\.)+[A-Za-z]+|\[(\d{3}\.?){4}\]|(\d{3}\.?){4}))"

    async def newsletterQuery(ctx):
        print("makes it here")
        while True:
            await ctx.author.send(embed = newsPrompt)

            def check(m):
                return m.author == ctx.author and m.channel.type == discord.ChannelType.private

            try:
                emailResp = await bot.wait_for('message', check = check, timeout = 300)
            except TimeoutError:
                print("User " + str(ctx.author) + " Timed out on subscription query; No changes to database" )
                await ctx.author.send(embed = timeout_embed)
                return False
            else:
                emailResp = emailResp.content
                veri = bool(regSearch.match(str(emailResp)))
                #print("passed regex")
                if veri:
                    msgPrompt = await ctx.author.send(embed = subConfirm(emailResp))
                    #print("sent")
                    thumbsup, thumbsdown = '👍','👎'
                    await msgPrompt.add_reaction(thumbsup)
                    await msgPrompt.add_reaction(thumbsdown)

                    def checkreact(reaction, react):
                        react = str(reaction.emoji)
                        return ((react == '👍' or react == '👎') and (reaction.message.id == msgPrompt.id))

                    await asyncio.sleep(.1)
                    try:
                        confirmation = await bot.wait_for('reaction_add', check = checkreact, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Timed out on subscription confirmation; No changes to database")
                        await ctx.author.send(embed = timeout_embed)
                        return False
                    else:
                        if str(confirmation[0].emoji) == '👍':
                            return emailResp

#========================================All User Commands================================

    @bot.command()
    @commands.cooldown(3,5)
    async def whitelist(ctx):
        if rconIp == "":
            await ctx.author.send("please run $setup before using any commmands")
            return False
        if ctx.channel.id == CHANNELID or CHANNELID == 0:
            if poll(ctx.author.id) == False:
                first_set = await query(ctx)
                #print("done with first set: " + str(first_set[0]) + str(first_set[1]) + str(first_set[2]) + str(first_set[3]))
                if first_set != False:
                    second_set = await newsletterQuery(ctx)
                    #print("done with second set: " + str(second_set))
                    if second_set != False:
                        cur.execute("INSERT INTO whitelist (user_id, first_name, last_name, uuid, username, email, isBanned) VALUES (?, ?, ?, ?, ?, ?, ?);" , (ctx.author.id, str(first_set[0]), str(first_set[1]), str(first_set[2]), str(first_set[3]), str(second_set), 0))
                        conn.commit()
                        mcr = MCRcon(str(rconIp), str(rconPass), port = int(rconPort))
                        mcr.connect()
                        resp = mcr.command("whitelist add " + str(first_set[3]))
                        print(resp)
                        mcr.disconnect()
                        await ctx.author.send(embed = addFinish_embed)
            else:
                if poll(ctx.author.id)[6] == 0:
                    await edit(ctx)


    @bot.command()
    @commands.cooldown(3,5)
    async def remove(ctx):
        if rconIp == "":
            await ctx.author.send("please run $setup before using any commmands")
            return False
        if ctx.channel.id == CHANNELID or CHANNELID == 0:
            if poll(ctx.author.id) != False:
                if poll(ctx.author.id)[6] == 0:
                    username = ctx.author
                    msgPrompt = await username.send(embed = removeConfirmPrompt_embed)
                    thumbsup, thumbsdown = '👍','👎'
                    await msgPrompt.add_reaction(thumbsup)
                    await msgPrompt.add_reaction(thumbsdown)

                    def checkreact(reaction, react):
                        react = str(reaction.emoji)
                        return ((react == '👍' or react == '👎') and (reaction.message.id == msgPrompt.id))

                    await asyncio.sleep(.1)
                    try:
                        confirmation = await bot.wait_for('reaction_add', check = checkreact, timeout = 300)
                    except TimeoutError:
                        print("User " + str(ctx.author) + "Timed out on removal confirmation, User remains in database")
                        await ctx.author.send(embed = timeout_embed)
                        return False
                    else:
                        if str(confirmation[0].emoji) == '👍':
                            mcUser = poll(username.id)[4]
                            mcr = MCRcon(str(rconIp), str(rconPass), port = int(rconPort))
                            mcr.connect()
                            resp = mcr.command("whitelist remove " + mcUser)
                            print(resp)
                            mcr.disconnect()
                            remove_player(username.id)
                            await username.send(embed = removeConfirm_embed)







    #Run the bot (must replace bot with own version) done in enviroment varibles
    token = str(os.environ.get('bot-token'))
    bot.run(token)
