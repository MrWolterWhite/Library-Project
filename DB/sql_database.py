from DB.database_interface import *
import sqlite3
import json
import random
import time

class SQLDatabase(Database):

	def __init__(self, filename: str = ""):
		self.filename = filename
		self.conn = None

	def is_table_exist(cursor, table_name):
		cursor.execute("""
			SELECT name FROM sqlite_master 
			WHERE type='table' AND name=?;
		""", (table_name,))

		return (cursor.fetchone() is not None)

	def __enter__(self):
		self.conn = sqlite3.connect(self.filename)
		self.cursor = self.conn.cursor()
		if not SQLDatabase.is_table_exist(self.cursor, "USERS"):
			table_creation_query = """
				CREATE TABLE USERS (
					UserID VARCHAR(50) PRIMARY KEY,
					Username VARCHAR(50),
					Password VARCHAR(50),
					Discord_id VARCHAR(50),
					reservations_ids TEXT
				);
			"""

			self.cursor.execute(table_creation_query)

		if not SQLDatabase.is_table_exist(self.cursor, "RESERVATIONS"):
			table_creation_query = """
				CREATE TABLE RESERVATIONS (
					ReservationID VARCHAR(10) PRIMARY KEY,
					Room TEXT,
					OwnerUserID VARCHAR(50),
					ReserverUserID VARCHAR(50),
					StartTime INT,
					Duration INT,
					Status TEXT
				);
			"""

			self.cursor.execute(table_creation_query)
		return self
		
	def __exit__(self):
		self.conn.close()
	
	def load_users(self) -> list[User]:
		self.cursor.execute("SELECT * FROM USERS")
		users = []
		for table_user in self.cursor.fetchall():
			user_id, username, password, discord_id, reservations_ids = tuple(table_user)
			reservations_ids = json.loads(reservations_ids)
			new_user: User = User(user_id, username, password, discord_id, reservations_ids)
			users.append(new_user)
		return users
	
	def load_user(self, user_id: str = "") -> User:
		self.cursor.execute("SELECT * FROM USERS WHERE UserID = ?", (user_id,))
		table_user = self.cursor.fetchone()
		if table_user is not None:
			user_id, username, password, discord_id, reservations_ids = tuple(table_user)
			reservations_ids = json.loads(reservations_ids)
			return User(user_id, username, password, discord_id, reservations_ids)
		else:
			return None
	
	def load_reservations(self) -> list[Reservation]:
		self.cursor.execute("SELECT * FROM RESERVATIONS")
		reservations = []
		for table_reservation in self.cursor.fetchall():
			reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str = tuple(table_reservation)
			room = Room(room_str)
			owner = self.load_user(owner_userid)
			reserver = self.load_user(reserver_userid)
			start_time = datetime.fromtimestamp(start_time_in_int)
			status = json.loads(status_str)
			reservation = Reservation(reservation_id, room, owner, reserver, start_time, duration, status)
			reservations.append(reservation)
		return reservations

	
	def load_reservations_of_user(self, user_id: str = "") -> list[Reservation]:
		'''fetches the reservations that are relevant for a certain user'''
		self.cursor.execute("SELECT * FROM RESERVATIONS WHERE OwnerUserID = ? or ReserverUserID = ?", (user_id, user_id))
		reservations = []
		for table_reservation in self.cursor.fetchall():
			reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str = tuple(table_reservation)
			room = Room(room_str)
			owner = self.load_user(owner_userid)
			reserver = self.load_user(reserver_userid)
			start_time = datetime.fromtimestamp(start_time_in_int)
			status = json.loads(status_str)
			reservation = Reservation(reservation_id, room, owner, reserver, start_time, duration, status)
			reservations.append(reservation)
		return reservations
	
	def is_at_most_X_hours_apart(date1: datetime, date2: datetime, x: int):
		return ((date1.timestamp() - date2.timestamp()) >= 60*60*x)
		
	def load_reservations_of_batch(self, start_time: datetime = datetime(1970, 1, 1)) -> list[Reservation]:
		'''fetches the reservations that are relevant for a certain time (and 
		the window of an hour forward)'''
		all_reservations: list[Reservation] = self.load_reservations()
		batch_reservations: list[Reservation] = []
		for reservation in all_reservations:
			if SQLDatabase.is_at_most_X_hours_apart(reservation.start_time, start_time, reservation.duration-1) and SQLDatabase.is_at_least_X_days_apart(reservation.start_time, start_time, 0):
				batch_reservations.append(reservation)
		return batch_reservations
			

	def is_same_day(date1: datetime, date2: datetime):
		if date1.day == date2.day and date1.month == date2.month and date1.year == date2.year:
			return True
		return False
	
	def is_at_least_X_days_apart(date1: datetime, date2: datetime, x: int):
		return ((date1.timestamp() - date2.timestamp()) >= 60*60*24*x)

	def is_legal_order(self, user: User, reservation: Reservation) -> bool:
		'''Returns if "user" is able to order the reservation on his name.
		A user can always reserve a room unless 
		
		- The reservation is for a time in the past
		- Someone already reserved it
		- The user already reserved a room in the same day
		- The user wants to make 3+ reservations in a window of a week'''
		if reservation.owner is not None or not SQLDatabase.is_at_least_X_days_apart(reservation.start_time, datetime.now(), 0):
			return False
		user_reservations = self.load_reservations_of_user(user.user_id)
		for user_reservation in user_reservations:
			user_reservation_day = datetime.date(user_reservation.start_time)
			reservation_day = datetime.date(reservation.start_time)
			if SQLDatabase.is_same_day(user_reservation_day, reservation_day):
				return False
		week_window_counter = 0
		for user_reservation in user_reservations:
			if not SQLDatabase.is_at_least_X_days_apart(reservation.start_time, user_reservation.start_time, 7) or not SQLDatabase.is_at_least_X_days_apart(user_reservation.start_time, reservation.start_time, 7):
				week_window_counter += 1
		for user_reservation in user_reservations:
			if SQLDatabase.is_at_least_X_days_apart(datetime.now(), user_reservation.start_time , 7):
				self.delete_reservation(user_reservation)
		if week_window_counter >= 2:
			return False
		return True


	
	def add_reservation(self, res_id: str = "", room_name: str = "", owner_userid: str = "", reserver_userid: str = "", date: datetime = datetime(1970, 1, 1), duration: int = 0, status: tuple = tuple()) -> str:
		'''Gets attributes of a reservation and adds it to the database'''
		date_to_int = int(date.timestamp())
		self.cursor.execute("INSERT INTO RESERVATIONS VALUES (?, ?, ?, ?, ?, ?, ?);",(res_id, room_name, owner_userid, reserver_userid, date_to_int, duration, json.dumps(status)))
		self.conn.commit()
	
	def add_user(self, username: str = "", password: str = "", discord_id: str = 
	""):
		'''Gets attributes of a user and adds it to the database'''
		user_id = discord_id
		reservations_ids = []
		self.cursor.execute("INSERT INTO USERS VALUES (?, ?, ?,?,?);",(user_id, username, password, discord_id, json.dumps(reservations_ids)))
		self.conn.commit()
		
	
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
		users = self.load_users()
		chosen_index = random.randint(0,len(users)-1)
		return users[chosen_index]
		
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
		
		if prioritize_myself and self.is_legal_order(myself, reservation):
			return myself
		is_legal = False
		user = User()
		
		TRIES = 50
		counter = 0
		
		while not is_legal and counter < TRIES:
			user = self.choose_potential_owner()
			is_legal = self.is_legal_order(user, reservation)
			counter += 1
		
		if is_legal:
			return user
		return None