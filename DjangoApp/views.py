import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import pymongo
import datetime

# Create your views here.

client = pymongo.MongoClient("mongodb+srv://student:student@weatherreadingsdb.hiue8df.mongodb.net/")
db = client["WeatherDataBase"]
Readings = db["Readings"]
Stations = db["Stations"]
Users = db["Users"]

def index(request):
    return HttpResponse("<h1>Welcome to <u>Weather App API<u>!</h1>")
def UsersView(request):
    if (request.method == "POST"):
        # Need to check privileges(parse username and password).
        body = json.loads(request.body.decode("uft-8"))
        if (Users.find_one({"username": body["username"]}) is None):
            return
        newUser = {
            "username": body["username"],
            "password": body["password"],
            "fname": body["fname"],
            "lname": body["lname"],
            "role": body["role"],
            "lastlogin": datetime.datetime.now(tz=datetime.timezone.utc)
        }
        result = Users.insert_one(newUser)
        data = {
            "inserted_id": str(result.inserted_id)
        }
        return JsonResponse(data, safe=False)
    if (request.method == "DELETE"):
        # Need to check privileges(parse username and password).
        body = json.loads(request.body.decode("uft-8"))
        userToDelete = {
            "username": body["username"]
        }
        if (Users.find_one(userToDelete) is None):
            return
        result = Users.delete_one(userToDelete)
        data = {
            "deleted_count": result.deleted_count
        }
        data = json.dumps(data)
        return JsonResponse(data, safe=False)
    if (request.method == "POST"):
        # Need to check privileges(parse username and password).
        body = json.loads(request.body.decode("uft-8"))
        userToChange = {
            "username": body["username"]
        }


        

        