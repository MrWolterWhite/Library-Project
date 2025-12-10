from datetime import datetime

class User:
	'''Represents a user in our app. The class will save the following 
	attributes for each user: username, password, discord_id, user_id and 
	week_window_reservations, which is a list that saves the ids of the reservations made 
	in the window of [now - week, now + week]'''

	def __init__(self, user_id: str = "", username: str = "", password: str = 
		"", discord_id: str = "", week_window_reservations_ids: list[str] = list()):
		...
		
	def is_legal_order(self, reservation: 'Reservation') -> bool:
		'''Returns if self is able to order the reservation on his name.
		A user can always reserve a room unless 
		
		- Someone already reserved it
		- The user already reserved a room in the same day
		- The user wants to make 3+ reservations in a window of a week'''
		...
		
class Room:
	'''Represents a room in the library. The class will save the following 
	attributes for each room: name, description'''

	def __init__(self, room_name: str = "", description: str = ""):
		...
		
class Reservation:
	'''Represents a reservation in our app. The class will save the following 
	attributes for each reservation: reservation_id, room (an instance of class 
	Room), the owner of the room, who reserved the room, start_time, duration 
	and status'''

	def __init__(self, reservation_id: str = "", room: Room = Room(), owner: 
	User = User(), who_reserved: User = User(), start_time: datetime = 
	datetime(1970,1,1), duration: int = 0, status: tuple = tuple()):
		...