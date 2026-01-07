from __future__ import annotations
from datetime import datetime
import time
import json
from constants import *

SECONDS_IN_HOUR = 60

class User:
	'''Represents a user in our app. The class will save the following 
	attributes for each user: username, password, discord_id, user_id and 
	week_window_reservations, which is a list that saves the ids of the reservations made 
	in the window of [now - week, now + week]'''

	def __init__(self, user_id: str = "", username: str = "", password: str = 
		"", discord_id: str = "", week_window_reservations_ids: list[str] = list()):
		self.user_id: str = user_id
		self.username: str = username
		self.password: str = password
		self.discord_id: str = discord_id
		self.week_window_reservations_ids: list[str] = week_window_reservations_ids
		
		
class Room:
	'''Represents a room in the library. The class will save the following 
	attributes for each room: name, description'''

	def __init__(self, room_name: str = "", description: str = ""):
		self.room_name: str = room_name
		self.description: str = description
	
class ReservationStatus:
	def __init__(self, status_code: int = INITIAL_RESERVATION_STATUS_CODE, reserved_duration: int = INITIAL_RESERVED_DURATION, description: str = ""):
		self.status_code: int = status_code
		self.reserved_duration: int = reserved_duration
		self.description: int = description

	def status_to_json_str(self) -> str:
		return json.dumps([self.status_code, self.reserved_duration, self.description])

	def json_str_to_status(stringified_json_self: str):
		status_list = json.loads(stringified_json_self)
		status_code, reserved_duration, description = tuple(status_list)
		return ReservationStatus(status_code, reserved_duration, description)

class Reservation:
	'''Represents a reservation in our app. The class will save the following 
	attributes for each reservation: reservation_id, room (an instance of class 
	Room), the owner of the room, who reserved the room, start_time, duration 
	and status'''

	def __init__(self, reservation_id: str = "", room: Room = Room(), owner: 
	User = User(), who_reserved: User = User(), start_time: datetime = 
	datetime(1970,1,1), duration: int = 0, status: ReservationStatus = ReservationStatus()):
		self.reservation_id: str = reservation_id
		self.room: Room = room
		self.owner: User = owner
		self.who_reserved: User = who_reserved
		self.start_time: datetime = start_time
		self.duration: int = duration
		self.status: ReservationStatus = status

	def filter_future_reservations(reservations: list[Reservation]):
		return_list = []
		for reservation in reservations:
			curr_time = int(time.time())
			reservation_end_time = int(int(reservation.start_time.timestamp()) + reservation.duration*SECONDS_IN_HOUR)
			if curr_time - reservation_end_time <= 0:
				return_list.append(reservation)
		return return_list
