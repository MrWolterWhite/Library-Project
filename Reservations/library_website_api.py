from DB.objects import Reservation
import requests
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

AFTER_LOGIN = "https://schedule.tau.ac.il/scilib/Web/schedule.php"

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