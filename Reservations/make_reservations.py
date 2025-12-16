import threading
from datetime import datetime
from DB.objects import *
from DB.sql_database import *
import requests
import json
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder
from constants import *

OFFSET_IN_DAYS = 7

AFTER_LOGIN = "https://schedule.tau.ac.il/scilib/Web/schedule.php"
SUBMIT_SPAM_AMOUNT = 20
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOURS = 60

room_translation_dict = {
"Room 013": 23,
"Room 014": 24,
"Room 015": 25,
"Room 016": 26,
"Room 018": 28,
"Room 019": 29,
"Room 108 - Upper Floor": 125,
"Room 109 - Upper Floor": 126,
"Room 110 - Upper Floor": 127,
"Room 111 - Upper Floor": 128,
"Study Booth 1 - Upper Floor": 129,
}

def is_date_28_2_on_leap_year(year: int, month: int, day: int):
	return (month == 2 and day == 28 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)))

def get_next_day(date: datetime):
	months_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	day = date.day
	month = date.month
	year = date.year
	if (day == (months_days[month-1] + 1)) or (day == months_days[month-1] and not is_date_28_2_on_leap_year(year, month, day)):
		day = 1
		if month == 12:
			month = 1
			year += 1
		else:
			month += 1
			return datetime(year, month, day)
	else:
		day += 1
		return datetime(year, month, day)
	
def get_X_days_later(date: datetime, x: int):
	return_date: datetime = date
	for _ in range(x):
		return_date = get_next_day(return_date)
	return return_date

def get_current_hour_for_reservation() -> datetime:
	'''Returns the date of the following batch of reservations (closest hour 
	plus a week, which is OFFSET_IN_DAYS days)'''
	curr_time = datetime.now()
	curr_time = datetime(curr_time.year, curr_time.month, curr_time.day, (curr_time.hour + 1) % 24, 0)
	return get_X_days_later(curr_time, OFFSET_IN_DAYS)

def login_to_library(session: requests.Session, reservation: Reservation):
	session.get("https://schedule.tau.ac.il/scilib/Web/index.php")
	payload = {'email': reservation.owner.username,
			'password': reservation.owner.password,
			"captcha": "",
			"login": "submit",
			"resume": AFTER_LOGIN,
			"language": "en_gb"}
	session.post('https://schedule.tau.ac.il/scilib/Web/index.php', data=payload)

def load_new_library_reservation(session: requests.Session, formatted_date: str = "", room_id: int = 0, isr_start_time: str = "", isr_end_time: str = "") -> tuple[str, int]:
	response = session.get(f"https://schedule.tau.ac.il/scilib/Web/reservation/?rid={room_id}&sid=3&rd={formatted_date}&sd={formatted_date} {isr_start_time}&ed={formatted_date} {isr_end_time}")
	csrf_token = response.text.split("const csrf")[1].split("\"")[1]
	user_id = int(response.text.split("const userId = ")[1].split(";")[0])
	session.headers.update({"X-Csrf-Token": csrf_token})
	session.get(f"https://schedule.tau.ac.il/scilib/Web/api/reservation.php?api=load&sd={formatted_date}+{isr_start_time}&ed={formatted_date}+{isr_end_time}&sid=3&rid={room_id}&rd={formatted_date}&rn=&pid=&srn=")
	return (csrf_token, user_id)

def load_existing_library_reservation(session: requests.Session, reference_number: str = "") -> tuple[str, int]:
	response = session.get(f"https://schedule.tau.ac.il/scilib/Web/reservation/?rn={reference_number}")
	csrf_token = response.text.split("const csrf")[1].split("\"")[1]
	user_id = int(response.text.split("const userId = ")[1].split(";")[0])
	session.headers.update({"X-Csrf-Token": csrf_token})
	session.get(f"https://schedule.tau.ac.il/scilib/Web/api/reservation.php?api=load&sd=&ed=&sid=&rid=&rd=&rn={reference_number}&pid=&srn=")
	return (csrf_token, user_id)

def post_reservation_attributes(session: requests.Session, formatted_date: str = "", room_id: int = 0, user_id: int = 0, etc_start_time: str = "", etc_end_time: str = "", duration: int = 0, reference_number: str = ""):
	payload = {"referenceNumber":reference_number,"ownerId":user_id,"resourceIds":[room_id],"accessories":[],"title":None,"description":None,"start":f"{formatted_date}T{etc_start_time}.000Z","end":f"{formatted_date}T{etc_end_time}.000Z","recurrence":{"type":"none","interval":duration,"weekdays":None,"monthlyType":None,"weekOfMonth":None,"terminationDate":None,"repeatDates":[]},"startReminder":None,"endReminder":None,"inviteeIds":[],"coOwnerIds":[],"participantIds":[],"guestEmails":[],"participantEmails":[],"allowSelfJoin":False,"attachments":[],"requiresApproval":False,"checkinDate":None,"checkoutDate":None,"termsAcceptedDate":None,"attributeValues":[],"meetingLink":None,"displayColor":None,"browserTimezone":"Asia/Jerusalem"}
	session.post('https://schedule.tau.ac.il/scilib/Web/api/reservation.php?api=attributes', json=payload)

def press_submit(session: requests.Session, formatted_date: str = "", room_id: int = 0, user_id: int = 0, csrf_token: str = "", etc_start_time: str = "", etc_end_time: str = "", duration: int = 0, reference_number: str = "") -> str:
	session.headers.update({"Accept": "application/json"})
	payload = MultipartEncoder(
		fields={"request": json.dumps({"reservation":{"referenceNumber":reference_number,"ownerId":user_id,"resourceIds":[room_id],"accessories":[],"title":None,"description":None,"start":f"{formatted_date}T{etc_start_time}.000Z","end":f"{formatted_date}T{etc_end_time}.000Z","recurrence":{"type":"none","interval":duration,"weekdays":None,"monthlyType":None,"weekOfMonth":None,"terminationDate":None,"repeatDates":[]},"startReminder":None,"endReminder":None,"inviteeIds":[],"coOwnerIds":[],"participantIds":[],"guestEmails":[],"participantEmails":[],"allowSelfJoin":False,"attachments":[],"requiresApproval":False,"checkinDate":None,"checkoutDate":None,"termsAcceptedDate":None,"attributeValues":[],"meetingLink":None,"displayColor":None,"browserTimezone":"Asia/Jerusalem"},"retryParameters":[],"updateScope":"full"}),
				"CSRF_TOKEN": csrf_token,
				"BROWSER_TIMEZONE": "Asia/Jerusalem"}
	)
	session.headers.update({"Content-Type": payload.content_type})

	response_order = session.post("https://schedule.tau.ac.il/scilib/Web/api/reservation.php?action=create", data=payload)
	return response_order.json()["data"]["referenceNumber"]

def wait_for_last_second_of_minute():
	is_time_to_submit = False
	while not is_time_to_submit:
		second_in_the_minute = int(time.time()) % SECONDS_IN_MINUTE
		if second_in_the_minute == (SECONDS_IN_MINUTE - 1):
			is_time_to_submit = True

if __name__ == "__main__":
	with SQLDatabase("library.db") as database:

		def handle_reservation(reservation: Reservation):
			'''Given a complete Reservation object, reserves or extends it
			The function also updates the database according to the result
			
			The function will - 
			- Make/Extend the reservation
			- Change the status of the reservation in the Reservations DB'''

			if database.is_new_reservation(reservation):
				reservation = reserve_new_room(reservation)
			else:
				reservation = continue_reserving_room(reservation)

			reservation.status[1] += 1 #TODO: fix. only if succeeded
			if reservation.status[1] == reservation.duration:
				reservation.status[0] = FINISHED_RESERVATIONS_STATUS_CODE
			database.update_reservation(reservation)

		def reserve_new_room(reservation: Reservation):
			'''Reserves a new reservation (without a reservation ID yet)
			Returns an updated reservation object (with the updated reservation ID)'''
			with requests.Session() as session:
				headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36", "Host": "schedule.tau.ac.il", "Origin": "https://schedule.tau.ac.il", "Referer": "https://schedule.tau.ac.il/scilib/Web/index.php"}
				session.headers = headers

				def to_2_digits(n):
					if n < 10:
						return f"0{n}"
					else:
						return str(n)

				isr_start_time = to_2_digits(reservation.start_time.hour) + ":00:00"
				isr_end_time = to_2_digits(reservation.start_time.hour + reservation.status[1] + 1) + ":00:00"

				TIME_DIFFERENCE = 2 #Should stay constant
				etc_start_time = to_2_digits((int(isr_start_time.split(":")[0]) - TIME_DIFFERENCE)) + ":00:00"
				etc_end_time = to_2_digits((int(isr_end_time.split(":")[0]) - TIME_DIFFERENCE)) + ":00:00"

				formatted_date = f"{reservation.start_time.year}-{reservation.start_time.month}-{reservation.start_time.day}"
				room_id = room_translation_dict[reservation.room.room_name]

				login_to_library(session, reservation)
				csrf_token, user_id = load_new_library_reservation(session, formatted_date, room_id, isr_start_time, isr_end_time)
				post_reservation_attributes(session, formatted_date, room_id, user_id, etc_start_time, etc_end_time, reservation.status[1], "")
				wait_for_last_second_of_minute()
				for _ in range(SUBMIT_SPAM_AMOUNT):
					reservation_id = press_submit(session, formatted_date, room_id, user_id, csrf_token, etc_start_time, etc_end_time, reservation.status[1], "")
					if reservation_id != "":
						print(reservation_id)
						reservation.reservation_id = reservation_id
				return reservation

		def continue_reserving_room(reservation: Reservation):
			with requests.Session() as session:
				headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36", "Host": "schedule.tau.ac.il", "Origin": "https://schedule.tau.ac.il", "Referer": "https://schedule.tau.ac.il/scilib/Web/index.php"}
				session.headers = headers

				def to_2_digits(n):
					if n < 10:
						return f"0{n}"
					else:
						return str(n)

				isr_start_time = to_2_digits(reservation.start_time.hour) + ":00:00"
				isr_end_time = to_2_digits(reservation.start_time.hour + reservation.status[1]) + ":00:00"

				TIME_DIFFERENCE = 2 #Should stay constant
				etc_start_time = to_2_digits((int(isr_start_time.split(":")[0]) - TIME_DIFFERENCE)) + ":00:00"
				etc_end_time = to_2_digits((int(isr_end_time.split(":")[0]) - TIME_DIFFERENCE)) + ":00:00"

				formatted_date = f"{reservation.start_time.year}-{reservation.start_time.month}-{reservation.start_time.day}"
				room_id = room_translation_dict[reservation.room.room_name]

				login_to_library(session, reservation)
				csrf_token, user_id = load_existing_library_reservation(session, reservation.reservation_id)
				post_reservation_attributes(session, formatted_date, room_id, user_id, etc_start_time, etc_end_time, reservation.status[1], reservation.reservation_id)
				wait_for_last_second_of_minute()
				for _ in range(SUBMIT_SPAM_AMOUNT):
					reservation_id = press_submit(session, formatted_date, room_id, user_id, csrf_token, etc_start_time, etc_end_time, reservation.status[1], reservation.reservation_id)
					if reservation_id != "":
						print(reservation_id)
						reservation.reservation_id = reservation_id
				return reservation

		def task():

			current_batch: list[Reservation] = database.load_reservations_of_batch(get_current_hour_for_reservation())
			threads = []
			
			for reservation in current_batch:
				new_thread = threading.Thread(target=handle_reservation, args=(reservation,))
				new_thread.start()
				threads.append(new_thread)
				
			for thread in threads:
				thread.join()
			
			#If I want to do something after the threads are finished
			
		# Execute task() every hour at XX:59
		while True:
			curr_time = int(time.time())
			time.sleep((SECONDS_IN_MINUTE*(MINUTES_IN_HOURS-1) + (SECONDS_IN_MINUTE*MINUTES_IN_HOURS) - (curr_time % SECONDS_IN_MINUTE*MINUTES_IN_HOURS)) % (SECONDS_IN_MINUTE*MINUTES_IN_HOURS)) #Sleep until 59th minute
			task()
			

