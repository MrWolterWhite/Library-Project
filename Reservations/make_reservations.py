import threading
from datetime import datetime
from DB.objects import *
from DB.sql_database import *
#every other necessary import

database = Database()

OFFSET_IN_DAYS = 7
PRIORITIZE_MYSELF = True

def get_current_hour_for_reservation() -> datetime:
	'''Returns the date of the following batch of reservations (closest hour 
	plus a week, which is OFFSET_IN_DAYS days)'''
	

def reserve_room(reservation: Reservation):
	'''Given a complete Reservation object, reserves or extends it
	The function also updates the database according to the result
	
	The function will need to - 
	
	- Make/Extend the reservation
	- Change the status of the reservation in the Reservations DB'''
	...

def task():

	current_batch: list[Reservation] = database.fetch_current_batch(get_current_hour_for_reservation())
	threads = []
	
	for reservation in current_batch:
		new_thread = threading.Thread(target=reserve_room, args=(reservation,))
		new_thread.start()
		threads.append(new_thread)
		
	for thread in threads:
		thread.join()
	
	#If I want to do something after the threads are finished
	
# Execute task() every hour at XX:00 (minus a couple of seconds to get ready)
	

