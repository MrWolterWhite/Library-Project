from datetime import datetime
from DB.objects import *
from DB.sql_database import *
from UI.md_styling import *
from dotenv import load_dotenv

import discord
from discord.ext import commands
import time
import asyncio
import os

PRIORITIZE_MYSELF = True
RESERVATION_INIT_STATUS = (0,0)

# Your bot token from the developer portal
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot with command prefix
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

with SQLDatabase("library.db") as app_database:

    def add_me(username: str = "", password: str = "", discord_id: str = ""):
        '''This method will add the user to the database or update his creds if he 
        is already signed up'''
        app_database.add_user(username, password, discord_id)

    def add_reservation(discord_id: str = "", room: Room = Room(), start_time: datetime = 
        datetime(1970,1,1), duration: int = 0):
        '''Creates a reservation object and updates the database. Makes sure to 
        update both the users and reservations database
        
        The function will need to - 
        
        - Create the Reservation object
        - Add the reservation to the Reservations database
        - Add this reservation to the owner's object
        - Add this reservation to the owner in the Users DB'''
        
        reservation: Reservation = Reservation(None, room, None, app_database.load_user(discord_id), start_time, duration, tuple()) #Create the Reservation object
        
        owner_user = app_database.find_owner(reservation, 
            myself = reservation.who_reserved,
            prioritize_myself = PRIORITIZE_MYSELF)
            
        if owner_user is None:
            # send_to_user("Couldn't make reservation") #Maybe add a description
            return
            
        reservation.owner = owner_user
        print(f"Owner is {reservation.owner.username}")
        
        #Update the database
        app_database.add_reservation(reservation.reservation_id, room.room_name, owner_user.user_id, reservation.who_reserved.user_id, start_time, duration, RESERVATION_INIT_STATUS)
        
    def my_reservations(discord_id: str = ""):
        '''Outputs all of the user's reservations'''
        return app_database.load_reservations_of_user(user_id = discord_id)
        
    def all_reservations():
        '''Outputs all of the reservations in the present / future made using this 
        app'''
        return app_database.load_reservations()

    def all_users():
        return app_database.load_users()

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')

    @bot.command()
    async def our_rooms(ctx):
        reservations = all_reservations()
        message = underline(bold("These are our reservations:")) + "\n"
        for reservation in reservations:
            message += (str(reservation))+"\n"
        await ctx.send(message)

    @bot.command()
    async def allusers(ctx):
        users = all_users()
        message = underline(bold("These are all of the users:")) + "\n"
        for user in users:
            message += (str(user))+"\n"
        await ctx.send(message)

    @bot.command()
    async def addme(ctx):
        username = ""
        password = ""

        await ctx.send(bold("What's your Username?"))
                    
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            username_msg = await bot.wait_for('message', check=check, timeout=30.0)
            await ctx.send(bold("Great! What's your Password?"))
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond!")
            return
        
        try:
            password_msg = await bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond!")
            return
        
        username = username_msg.content
        password = password_msg.content
        
        try:
            add_me(username, password, ctx.author.id)
        except Exception as e:
            await ctx.send("Something went wrong! try again in a few moments..")
            print(f"Exception in discord_bot.py, line 118: {e}")
        else:
            await ctx.send(bold("User added/modified successfully!"))
        

    @bot.command()
    async def reserve(ctx):
        #TODO: Add checks for the inputs
        room_name = ""
        start_time = datetime(1970, 1, 1)
        duration = 0

        await ctx.send(bold("What Room do you want to Reserve?"))
                    
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            room_msg = await bot.wait_for('message', check=check, timeout=300.0)
            await ctx.send(bold("When do you want to reserve it? (DD/MM/YYYY HH:MM, MM == 0 only)"))
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond!")
            return
        
        try:
            starttime_msg = await bot.wait_for('message', check=check, timeout=300.0)
            await ctx.send(bold("How many hours do you want to reserve the room for?"))
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond!")
            return
        
        try:
            duration_msg = await bot.wait_for('message', check=check, timeout=300.0)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond!")
            return
        
        room_name = room_msg.content
        room = Room(room_name)
        date_part, time_part = starttime_msg.content.split(" ")[:2]
        day, month, year = date_part.split("/")
        day = int(day)
        month = int(month)
        year = int(year)
        hour = int(time_part.split(":")[0])
        start_time = datetime(year, month, day, hour)
        duration = int(duration_msg.content)
        
        try:
            add_reservation(ctx.author.id, room, start_time, duration)
        except Exception as e:
            await ctx.send("Something went wrong! try again in a few moments..")
            print(f"Exception in bot.py, line 170: {e}")
        else:
            await ctx.send(bold("Reservation added successfully!"))

    bot.run(TOKEN)