from DB.database_interface import *
import sqlite3
import json

RESERVATION_INIT_STATUS = (0,0)

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
					StartTime INT
					Duration INT
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
		
	def load_reservations_of_batch(self, start_time: datetime = datetime(1970, 1, 1)) -> list[Reservation]:
		'''fetches the reservations that are relevant for a certain time (and 
		the window of an hour forward)'''
		...
	
	def add_reservation(self, res_id: str = "", room_name: str = "", owner_userid: str = "", reserver_userid: str = "", date: datetime = datetime(1970, 1, 1), duration: int = 0) -> str:
		'''Gets attributes of a reservation and adds it to the database'''
		date_to_int = int(date.timestamp())
		self.cursor.execute("INSERT INTO RESERVATIONS VALUES (?, ?, ?, ?, ?, ?, ?);",(res_id, room_name, owner_userid, reserver_userid, date_to_int, duration, RESERVATION_INIT_STATUS))
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