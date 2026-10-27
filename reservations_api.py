"""
mock_room_reservation_api.py

A tiny mock backend for a room reservation system: browse rooms (study
rooms, conference rooms, labs), see which time slots are open today,
book/cancel a reservation, and read room-related announcements
(closures, maintenance, etc).

Run with:
    pip install fastapi uvicorn
    python reservations_api.py

API is available at http://localhost:8004

Endpoints:
    GET  /rooms
    GET  /rooms/{room_id}
    GET  /rooms/{room_id}/slots
    GET  /my-reservations
    POST /reservations/book     body: {"room_id": int, "slot": str}
    POST /reservations/cancel   body: {"reservation_id": int}
    GET  /announcements
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Mock Room Reservation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NOW = datetime(2026, 8, 23, 9, 0, 0)
TODAY = NOW.date().isoformat()

# Every room offers the same fixed set of one-hour slots today.
SLOTS = [
    "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00",
    "13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00",
]

# ---------------------------------------------------------------------
# In-memory "database"
# ---------------------------------------------------------------------

ROOMS = [
    {"id": 1, "name": "Study Room 204", "building": "Library", "capacity": 4, "type": "study", "equipment": "whiteboard"},
    {"id": 2, "name": "Study Room 210", "building": "Library", "capacity": 6, "type": "study", "equipment": "whiteboard, TV"},
    {"id": 3, "name": "Conference Room A", "building": "Student Union", "capacity": 12, "type": "conference", "equipment": "projector, video conferencing"},
    {"id": 4, "name": "Media Lab 1", "building": "Arts Building", "capacity": 8, "type": "lab", "equipment": "editing workstations"},
    {"id": 5, "name": "Group Study Pod C", "building": "Library", "capacity": 2, "type": "study", "equipment": "none"},
]

# Reservations for the (single, demo) logged-in user and everyone else,
# all mixed together in one list -- this mock has no real auth.
RESERVATIONS = [
    {"id": 1, "room_id": 1, "date": TODAY, "slot": "10:00-11:00", "reserved_by": "you"},
    {"id": 2, "room_id": 3, "date": TODAY, "slot": "13:00-14:00", "reserved_by": "Dolly Parton"},
]
_next_reservation_id = 3

ANNOUNCEMENTS = [
    {
        "id": 1,
        "title": "Media Lab 1 closed for equipment upgrades",
        "posted": "2026-08-21T10:00:00",
        "body": "Media Lab 1 will be unavailable for booking next Tuesday while new editing workstations are installed.",
    },
    {
        "id": 2,
        "title": "New group study pods added",
        "posted": "2026-08-18T10:00:00",
        "body": "Three new two-person study pods are now bookable on the library's second floor, including Group Study Pod C.",
    },
]


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

class BookRequest(BaseModel):
    room_id: int
    slot: str


class CancelRequest(BaseModel):
    reservation_id: int


def _get_room_or_404(room_id: int) -> dict:
    for room in ROOMS:
        if room["id"] == room_id:
            return room
    raise HTTPException(status_code=404, detail="Room not found")


def _slot_reservation(room_id: int, slot: str):
    for r in RESERVATIONS:
        if r["room_id"] == room_id and r["date"] == TODAY and r["slot"] == slot:
            return r
    return None


@app.get("/rooms")
def list_rooms():
    return ROOMS


@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    return _get_room_or_404(room_id)


@app.get("/rooms/{room_id}/slots")
def get_room_slots(room_id: int):
    _get_room_or_404(room_id)
    result = []
    for slot in SLOTS:
        existing = _slot_reservation(room_id, slot)
        result.append({
            "slot": slot,
            "status": "reserved" if existing else "available",
            "reserved_by": existing["reserved_by"] if existing else None,
            "reservation_id": existing["id"] if existing else None,
        })
    return result


@app.get("/my-reservations")
def get_my_reservations():
    mine = [r for r in RESERVATIONS if r["reserved_by"] == "you"]
    enriched = []
    for r in mine:
        room = _get_room_or_404(r["room_id"])
        enriched.append({**r, "room_name": room["name"], "building": room["building"]})
    return enriched


@app.get("/announcements")
def list_announcements():
    return ANNOUNCEMENTS


@app.post("/reservations/book")
def book_reservation(req: BookRequest):
    global _next_reservation_id
    _get_room_or_404(req.room_id)
    if req.slot not in SLOTS:
        raise HTTPException(status_code=400, detail="Not a valid time slot")
    if _slot_reservation(req.room_id, req.slot):
        raise HTTPException(status_code=400, detail="That slot is already reserved")

    new_reservation = {
        "id": _next_reservation_id,
        "room_id": req.room_id,
        "date": TODAY,
        "slot": req.slot,
        "reserved_by": "you",
    }
    RESERVATIONS.append(new_reservation)
    _next_reservation_id += 1
    return new_reservation


@app.post("/reservations/cancel")
def cancel_reservation(req: CancelRequest):
    for i, r in enumerate(RESERVATIONS):
        if r["id"] == req.reservation_id:
            RESERVATIONS.pop(i)
            return {"cancelled": req.reservation_id}
    raise HTTPException(status_code=404, detail="Reservation not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8004)