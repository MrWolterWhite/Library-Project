import discord
from discord import app_commands, ui
from typing import Optional
from datetime import datetime, timedelta
from constants import *
import json

class AddMeModal(ui.Modal, title='📝 User Sign Up'):
    def __init__(self, *, title = '📝 User Sign Up', signup_func = None):
        super().__init__(title=title)
        self.signup_func = signup_func

    username = ui.TextInput(
        label='Username',
        placeholder='Enter your library username',
        style=discord.TextStyle.short,
        max_length=100
    )
    password = ui.TextInput(
        label='Password',
        placeholder='Enter your password',
        style=discord.TextStyle.short,
        min_length=0
    )

    async def on_submit(self, interaction: discord.Interaction):
        success = await self.signup_func(str(self.username), str(self.password), str(interaction.user.id))
        
        if success:
            embed = discord.Embed(
                title='✅ Sign Up Successful',
                description=f'User **{self.username}** has been registered.',
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title='❌ Sign Up Failed',
                description='Could not register user. Username might be taken.',
                color=discord.Color.red()
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# STEP 1 VIEW: Initial Selection (Room, Date, Time)

class ReservationStarter(ui.View):
    def __init__(self, user_id: int, add_reservation_func):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_reservation_func = add_reservation_func
        self.room: Optional[str] = None
        self.date: Optional[str] = None
        self.time: Optional[int] = None

    def update_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Step 1/2: Select Time & Place",
            description="Start by choosing the **Room**, **Date**, and **Hour**.",
            color=discord.Color.blurple()
        )
        return embed

    @ui.select(
        placeholder="Select Room...",
        options=[discord.SelectOption(label=r) for r in ROOM_OPTIONS]
    )
    async def room_select(self, interaction: discord.Interaction, select: ui.Select):
        self.room = select.values[0]
        select.placeholder = self.room
        await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @ui.select(
        placeholder="Select Date...",
        options=[
            discord.SelectOption(label=f"Today ({datetime.now():%Y-%m-%d})", value=datetime.now().strftime('%Y-%m-%d')),
            discord.SelectOption(label=f"Tomorrow ({(datetime.now() + timedelta(days=1)):%Y-%m-%d})", value=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')),
            discord.SelectOption(label=f"Day After ({(datetime.now() + timedelta(days=2)):%Y-%m-%d})", value=(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')),
        ]
    )
    async def date_select(self, interaction: discord.Interaction, select: ui.Select):
        self.date = select.values[0]
        select.placeholder = self.date
        await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @ui.select(
        placeholder="Select Start Hour...",
        options=[discord.SelectOption(label=f"{h}:00", value=str(h)) for h in range(8, 20)]
    )
    async def time_select(self, interaction: discord.Interaction, select: ui.Select):
        self.time = int(select.values[0])
        select.placeholder = str(f"{self.time}:00")
        await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @ui.button(label="Next Step ➡️", style=discord.ButtonStyle.primary, row=4)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        if not all([self.room, self.date, self.time]):
            await interaction.response.send_message("⚠️ Please select Room, Date, and Time first.", ephemeral=True)
            return
        
        # Transition to View 2
        # We pass the collected data to the next view
        view_2 = ReservationFinisher(self.user_id, self.room, self.date, self.time, add_reservation_func=self.add_reservation_func)
        
        # Update the existing message with the new View and Embed
        await interaction.response.edit_message(embed=view_2.update_embed(), view=view_2)

# --- STEP 2 VIEW: Final Details (Duration & Repeat) ---

class ReservationFinisher(ui.View):
    def __init__(self, user_id: int, room: str, date: str, time: int, add_reservation_func):
        super().__init__(timeout=300)
        self.add_reservation_func = add_reservation_func
        self.user_id = user_id
        self.room = room
        self.date = date
        self.time = time
        # Data to collect in Step 2
        self.duration: Optional[int] = None
        self.repeat: Optional[tuple[str,int]] = None

    def update_embed(self) -> discord.Embed:
        # Create a pretty timestamp
        dt_obj = datetime.strptime(f"{self.date} {self.time}:00:00", '%Y-%m-%d %H:%M:%S')
        
        desc = (
            f"**Selected:** {self.room}\n"
            f"**Start Time:** {dt_obj.strftime('%A, %b %d')} at {self.time}:00\n"
            "-----------------------------\n"
            "Please select **Duration** and **Repetition** to finish."
        )

        embed = discord.Embed(
            title="Step 2/2: Finalize Reservation",
            description=desc,
            color=discord.Color.blue()
        )
        
        return embed

    @ui.select(
        placeholder="Select Duration...",
        options=[discord.SelectOption(label=(f"{duration} hours" if duration != 1 else f"{duration} hour"), value=str(duration)) for duration in DURATION_OPTIONS]
    )
    async def duration_select(self, interaction: discord.Interaction, select: ui.Select):
        self.duration = int(select.values[0])
        select.placeholder = (f"{self.duration} hours" if self.duration != 1 else f"{self.duration} hour")
        await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @ui.select(
        placeholder="Select Repetition...",
        options=[discord.SelectOption(label=key, value=json.dumps(val)) for key, val in REPEAT_OPTIONS.items()]
    )
    async def repeat_select(self, interaction: discord.Interaction, select: ui.Select):
        self.repeat = json.loads(select.values[0])
        select.placeholder = self.repeat[0]
        await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @ui.button(label="Confirm Booking ✅", style=discord.ButtonStyle.green, row=2)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if not self.duration or not self.repeat:
            await interaction.response.send_message("⚠️ Please select both Duration and Repeat options.", ephemeral=True)
            return

        # Disable buttons to prevent double click
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        # Build DateTime object
        reservation_dt = datetime.strptime(f"{self.date} {self.time}:00:00", '%Y-%m-%d %H:%M:%S')
        year, month, day = self.date.split("-")
        reservation_date_datetime = datetime(int(year), int(month), int(day))

        # Insert to DB
        success = await self.add_reservation_func(
            self.user_id,
            self.room,
            reservation_date_datetime,
            self.duration,
            repeat=self.repeat[1]
        )

        if success:
            embed = discord.Embed(title="✅ Reservation Confirmed!", color=discord.Color.green())
            embed.description = (
                f"**Room:** {self.room}\n"
                f"**When:** {reservation_dt.strftime('%Y-%m-%d %H:%M')}\n"
                f"**Duration:** {self.duration}h\n"
                f"**Repeat:** {self.repeat[0]}"
            )
            # Replace the form with the success message
            await interaction.edit_original_response(embed=embed, view=None)
            # await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="❌ Reservation Failed", description="Room unavailable or DB error.", color=discord.Color.red())
            await interaction.edit_original_response(embed=embed, view = None)
        
        
        self.stop()


