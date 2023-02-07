from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import urllib

DATABASE_NAME = "exceed01"
COLLECTION_NAME = "reservation"

load_dotenv(".env")
user = os.getenv("username")
password = urllib.parse.quote(os.getenv("password"))

MONGO_DB_URL = f'mongodb://{user}:{urllib.parse.quote(password)}@mongo.exceed19.online:8443/?authMechanism=DEFAULT'

client = MongoClient(MONGO_DB_URL)

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]


class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


app = FastAPI()

def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0

@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name: str):
    list_name = []
    for i in collection.find({'name': f'{name}'}, {"_id": False}):
        list_name.append(i)
    return {"result": list_name}


@app.get("/reservation/by-room/{room_id}", status_code=200)
def get_reservation_by_room(room_id: int):
    list_room = []
    for i in collection.find({'room_id': room_id}, {"_id": False}):
        list_room.append(i)
    return {"result": list_room}


@app.post("/reservation", status_code=200)
def reserve(reservation: Reservation):
    if not room_avaliable(reservation.room_id, str(reservation.start_date), str(reservation.end_date)):
        raise HTTPException(status_code=400)
    if reservation.start_date > reservation.end_date:
        raise HTTPException(status_code=400)
    if reservation.room_id not in range(1, 11):
        raise HTTPException(status_code=400)
    collection.insert_one({
            "name": reservation.name,
            "start_date": str(reservation.start_date),
            "end_date": str(reservation.end_date),
            "room_id": reservation.room_id
        })


@app.put("/reservation/update", status_code=200)
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    filter_update = {
        "name": reservation.name,
        "start_date": str(reservation.start_date),
        "end_date": str(reservation.end_date),
        "room_id": reservation.room_id
    }
    update = {'$set': {"start_date": str(new_start_date), "end_date": str(new_end_date)}}
    if not room_avaliable(reservation.room_id, str(new_start_date), str(new_end_date)):
        raise HTTPException(status_code=400)
    if new_start_date > new_end_date:
        raise HTTPException(status_code=400)
    if room_avaliable(reservation.room_id,
                        new_start_date.isoformat(),
                        new_end_date.isoformat()) and new_start_date < new_end_date:
        collection.update_one(filter_update, update)


@app.delete("/reservation/delete", status_code=200)
def cancel_reservation(reservation: Reservation):
    collection.delete_one({
        "name": reservation.name,
        "start_date": str(reservation.start_date),
        "end_date": str(reservation.end_date),
        "room_id": reservation.room_id
    })
