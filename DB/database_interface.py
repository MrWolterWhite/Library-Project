from DB.objects import *
from datetime import datetime

class Database():

	def __init__(self):
		...
	
	def load_users(self) -> list[User]:
		...
	
	def load_user(self, user_id: str = "") -> User:
		...
	
	def load_reservations(self) -> list[Reservation]:
		...
	
	def load_reservations_of_user(self, user_id: str = "") -> list[Reservation]:
		'''fetches the reservations that are relevant for a certain user'''
		...
		
	def load_reservations_of_batch(self, start_time: datetime = datetime(1970, 
	1, 1)) -> list[Reservation]:
		'''fetches the reservations that are relevant for a certain time (and 
		the window of an hour forward)'''
		...
	
	def add_reservation(self, res_id: str = "", room_name: str = "", owner: str 
	= "", date: datetime = datetime(1970, 1, 1), duration: int = 0) -> str:
		'''Gets attributes of a reservation and adds it to the database'''
		...
	
	def add_user(self, username: str = "", password: str = "", discord_id: str = 
	""):
		...
		'''Gets attributes of a user and adds it to the database'''
	
	def update_reservation(self, res_id: str = "", room_name: str = "", owner: 
	str = "", date: datetime = datetime(1970, 1, 1), duration: int = 0, 
		hours_already_reserved: int = 0):
		...
	
	def delete_user(self, user_id: str = ""):
		...
		
	def delete_reservation(self, reservation_id: str = ""):
		...
		
	def choose_potential_owner(self):
		'''Chooses a potential owner, i.e random choice'''
		...
		
	def find_owner(self, reservation: Reservation = Reservation(), myself: User 
	= User(), prioritize_myself: bool = True) -> User:
		'''Given a reservation, finds a user that can be the owner of that 
		reservation and returns it. The argument prioritize_myself is a boolean 
		variable that controls how we prioritize the choice. If the variable is 
		True, then we prefer to order the reservation on our name, if possible.
		If it's False, then we don't care.
		
		If we can't find an owner, we will return None'''
		
		if reservation.owner is not None:
			return reservation.owner
		
		if prioritize_myself and myself.is_legal_order(reservation):
			return myself
		is_legal = False
		user = User()
		
		TRIES = 50
		counter = 0
		
		while not is_legal and counter < TRIES:
			user = self.choose_potential_owner()
			is_legal = user.is_legal_order(reservation)
			counter += 1
		
		if is_legal:
			return user
		return None