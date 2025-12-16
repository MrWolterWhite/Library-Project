from DB.objects import *

ROOM_OPTIONS = ["Room 013", "Room 014", "Room 015", "Room 016", "Room 018", "Room 019", "Room 108 - Upper Floor", "Room 109 - Upper Floor", "Room 110 - Upper Floor", "Room 111 - Upper Floor", "Study Booth 1 - Upper Floor"]
DURATION_OPTIONS = [1, 2, 3]
LIBRARY_OPENING_HOUR = 8
LIBRARY_CLOSING_HOUR = 21
REPEAT_OPTIONS = {
    "No Repeat": ("No Repeat", 0),
    "Every Week": ("Every Week", 1),
    "Every 2 Weeks": ("Every 2 Weeks", 2),
    "Every Month": ("Every Month", 4)
}
FAILED_RESERVATION_STATUS_CODE = 3
FINISHED_RESERVATIONS_STATUS_CODE = 2
PENDING_RESERVATION_STATUS_CODE = 1
INITIAL_RESERVATION_STATUS_CODE = 0
INITIAL_RESERVED_DURATION = 0
RESERVATION_INIT_STATUS = ReservationStatus(INITIAL_RESERVATION_STATUS_CODE, INITIAL_RESERVED_DURATION, "")