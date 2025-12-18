from DB.database_interface import *
import sqlite3
import json
import random
from constants import *

INITIALIZING_PREFIX = "INIT"

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
					ReservationID VARCHAR(50) PRIMARY KEY,
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
			reservations_ids: list = json.loads(reservations_ids)
			new_user: User = User(user_id, username, password, discord_id, reservations_ids)
			users.append(new_user)
		return users
	
	def load_user_by_id(self, user_id: str = "") -> User:
		self.cursor.execute("SELECT * FROM USERS WHERE UserID = ?", (user_id,))
		table_user = self.cursor.fetchone()
		if table_user is not None:
			user_id, username, password, discord_id, reservations_ids = tuple(table_user)
			reservations_ids = json.loads(reservations_ids)
			return User(user_id, username, password, discord_id, reservations_ids)
		else:
			return None
		
	def table_reservation_to_reservation_object(self, reservation_id: str = "", room_str: str = "", owner_userid: str = "", reserver_userid: str = "", start_time_in_int: int = 0, duration: int = 0, status_str: str = ""):
		room = Room(room_str)
		owner = self.load_user_by_id(owner_userid)
		reserver = self.load_user_by_id(reserver_userid)
		start_time = datetime.fromtimestamp(start_time_in_int)
		status: ReservationStatus = ReservationStatus.json_str_to_status(status_str)
		return Reservation(reservation_id, room, owner, reserver, start_time, duration, status)
	
	def load_reservations(self, only_future: bool = False) -> list[Reservation]:
		self.cursor.execute("SELECT * FROM RESERVATIONS")
		reservations = []
		for table_reservation in self.cursor.fetchall():
			reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str = tuple(table_reservation)
			reservation = SQLDatabase.table_reservation_to_reservation_object(self, reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str)
			reservations.append(reservation)
		if only_future:
			return Reservation.filter_future_reservations(reservations)
		return reservations

	
	def load_reservations_of_user(self, user_id: str = "", only_future: bool = False) -> list[Reservation]:
		'''fetches the reservations that are relevant for a certain user'''
		self.cursor.execute("SELECT * FROM RESERVATIONS WHERE OwnerUserID = ? or ReserverUserID = ?", (user_id, user_id))
		reservations = []
		for table_reservation in self.cursor.fetchall():
			reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str = tuple(table_reservation)
			reservation = SQLDatabase.table_reservation_to_reservation_object(reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str)
			reservations.append(reservation)
		if only_future:
			return Reservation.filter_future_reservations(reservations)
		return reservations
	
	def load_reservation_by_id(self, reservation_id: str = "") -> Reservation | None:
		self.cursor.execute("SELECT * FROM RESERVATIONS WHERE ReservationID = ?", (reservation_id,))
		reservations = []
		for table_reservation in (self.cursor.fetchall() or []):
			reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str = tuple(table_reservation)
			reservation = SQLDatabase.table_reservation_to_reservation_object(reservation_id, room_str, owner_userid, reserver_userid, start_time_in_int, duration, status_str)
			reservations.append(reservation)
		if len(reservations) == 0:
			return None
		return reservations[0]
	
	def is_at_most_X_hours_apart(date1: datetime, date2: datetime, x: int):
		return ((date1.timestamp() - date2.timestamp()) >= 60*60*x)
		
	def load_reservations_of_batch(self, start_time: datetime = datetime(1970, 1, 1)) -> list[Reservation]:
		'''fetches the reservations that are relevant for a certain time (and 
		the window of an hour forward)'''
		all_reservations: list[Reservation] = self.load_reservations()
		batch_reservations: list[Reservation] = []
		for reservation in all_reservations:
			if reservation.status.status_code != FAILED_RESERVATION_STATUS_CODE and SQLDatabase.is_at_most_X_hours_apart(reservation.start_time, start_time, reservation.duration) and SQLDatabase.is_at_least_X_days_apart(reservation.start_time, start_time, 0):
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
		if reservation.owner is not None or not SQLDatabase.is_at_least_X_days_apart(reservation.start_time, datetime.now(), -1/24):
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

	def add_reservation(self, res_id: str = "", room_name: str = "", owner_userid: str = "", reserver_userid: str = "", date: datetime = datetime(1970, 1, 1), duration: int = 0, status: ReservationStatus = ReservationStatus()) -> str:
		'''Gets attributes of a reservation and adds it to the database'''
		date_to_int = int(date.timestamp())
		self.cursor.execute("INSERT INTO RESERVATIONS VALUES (?, ?, ?, ?, ?, ?, ?);",(res_id, room_name, owner_userid, reserver_userid, date_to_int, duration, status))
		self.conn.commit()
		#TODO: Update the owner's reservations
	
	def add_user(self, username: str = "", password: str = "", discord_id: str = 
	""):
		'''Gets attributes of a user and adds it to the database'''
		user_id = discord_id
		reservations_ids = []
		self.cursor.execute("INSERT INTO USERS VALUES (?, ?, ?,?,?);",(user_id, username, password, discord_id, json.dumps(reservations_ids)))
		self.conn.commit()
		
	def make_new_reservation_id(self, reservation: Reservation):
		return f"{INITIALIZING_PREFIX}{reservation.owner.user_id}{reservation.start_time.date().strftime('%Y.%m.%d')}"
	
	def is_new_reservation(self, reservation: Reservation):
		res_id = reservation.reservation_id
		return ((len(res_id) >= len(INITIALIZING_PREFIX)) and res_id[:INITIALIZING_PREFIX] == INITIALIZING_PREFIX)

	def update_reservation(self, reservation: Reservation):
		if self.load_reservation_by_id(reservation.reservation_id) is None:
			#The reservation is saved with an initialized name
			self.delete_reservation(self.make_new_reservation_id(reservation))
			self.add_reservation(reservation.reservation_id, reservation.room.room_name, reservation.owner.user_id, reservation.who_reserved.user_id, reservation.start_time, reservation.duration, reservation.status.status_to_json_str())
		
		self.cursor.execute("UPDATE RESERVATIONS SET Room = ?, OwnerUserID = ?, ReserverUserID = ?, StartTime = ?, Duration = ?, Status = ? WHERE ReservationID = ?;",(reservation.room.room_name, reservation.owner.user_id, reservation.who_reserved.user_id, int(reservation.start_time.timestamp()), reservation.duration, json.dumps(reservation.status), reservation.reservation_id))
		self.conn.commit()
		
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