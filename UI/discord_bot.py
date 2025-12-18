from datetime import datetime
from DB.objects import *
from DB.sql_database import *
from UI.md_styling import *
from dotenv import load_dotenv
import discord
import os
from discord import app_commands, ui
from UI.discord_ui_objects import *
from constants import *

PRIORITIZE_MYSELF = True
RESERVATION_INIT_STATUS = ReservationStatus(INITIAL_RESERVATION_STATUS_CODE, INITIAL_RESERVED_DURATION, "")

if __name__ == "__main__":

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    class MyClient(discord.Client):
        def __init__(self, *, intents: discord.Intents):
            super().__init__(intents=intents)
            self.tree = app_commands.CommandTree(self)

        async def on_ready(self):
            print(f'Logged in as {self.user} (ID: {self.user.id})')
            await self.tree.sync()
            print('✅ Commands synced globally.')

    intents = discord.Intents.default()
    client = MyClient(intents=intents)

    with SQLDatabase("library.db") as app_database:

        async def add_me(username: str = "", password: str = "", discord_id: str = ""):
            '''This method will add the user to the database or update his creds if he 
            is already signed up'''
            try:
                app_database.add_user(username, password, discord_id)
            except Exception as e:
                return False
            else:
                return True

        async def add_reservation(discord_id: str = "", room_name: str = '', start_time: datetime = 
            datetime(1970,1,1), duration: int = 0, repeat: int = 0):
            '''Creates a reservation object and updates the database. Makes sure to 
            update both the users and reservations database
            
            The function will need to - 
            
            - Create the Reservation object
            - Add the reservation to the Reservations database
            - Add this reservation to the owner's object
            - Add this reservation to the owner in the Users DB'''
            
            try:
                room: Room = Room(room_name=room_name)
                reservation: Reservation = Reservation(None, room, None, app_database.load_user_by_id(discord_id), start_time, duration, ReservationStatus()) #Create the Reservation object
                
                owner_user = app_database.find_owner(reservation, 
                    myself = reservation.who_reserved,
                    prioritize_myself = PRIORITIZE_MYSELF)
                    
                if owner_user is None:
                    # send_to_user("Couldn't make reservation") #Maybe add a description
                    return False
                    
                reservation.owner = owner_user
                reservation.reservation_id = app_database.make_new_reservation_id(reservation)
                print(f"Owner is {reservation.owner.username}")
                
                #Update the database
                app_database.add_reservation(reservation.reservation_id, room.room_name, owner_user.user_id, reservation.who_reserved.user_id, start_time, duration, RESERVATION_INIT_STATUS.status_to_json_str())
            except Exception as e:
                return False
            return True
            
        async def my_reservations(discord_id: str = ""):
            '''Outputs all of the user's reservations'''
            return app_database.load_reservations_of_user(user_id = discord_id)
            
        async def all_reservations():
            '''Outputs all of the reservations in the present / future made using this 
            app'''
            return app_database.load_reservations()

        async def all_users():
            return app_database.load_users()

        @client.tree.command(name="addme", description="Register your account")
        async def addme_command(interaction: discord.Interaction):
            await interaction.response.send_modal(AddMeModal(signup_func=add_me))

        @client.tree.command(name="reserve", description="Book a new room reservation")
        async def reserve_command(interaction: discord.Interaction):
            view = ReservationStarter(interaction.user.id, add_reservation_func=add_reservation)
            await interaction.response.send_message(embed=view.update_embed(), view=view, ephemeral=True)

        @client.tree.command(name="ourrooms", description="Load our room reservation")
        async def our_rooms_command(interaction: discord.Interaction):
            reservations: list[Reservation] = app_database.load_reservations()
            user_ids = [reservation.owner.username for reservation in reservations]
            room_names = [reservation.room.room_name for reservation in reservations]
            dates = [reservation.start_time for reservation in reservations]
            durations = [reservation.duration for reservation in reservations]
            view = reservationsSummary(user_ids, room_names, dates, durations)
            await interaction.response.send_message(embed=view.update_embed(), view=view, ephemeral=True)

        client.run(TOKEN)