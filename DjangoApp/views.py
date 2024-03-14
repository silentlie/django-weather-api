import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import pymongo
import datetime
import hashlib
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
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        if (result is None or result["Role"] != "Admin"):
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        newUser = {
            "Username": body["Username"],
            "Password": Hash_Password(body["Password"]),
            "FName": body["FName"],
            "LName": body["LName"],
            "Role": body["Role"],
            "LastLogin": datetime.datetime.now(tz=datetime.timezone.utc),
            "Token": "",
        }
        result = Users.insert_one(newUser)
        data = {
            "Inserted_id": str(result.inserted_id)
        }
        return JsonResponse(data, safe=False, status=200)
    if (request.method == "DELETE"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        if (result is None or result["Role"] != "Admin"):
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        userToDelete = {
            "Username": body["Username"]
        }
        if (Users.find_one(userToDelete) is None):
            return JsonResponse({"Success": False, "Message": "Couldn't Find Username"}, status=404)
        result = Users.delete_one(userToDelete)
        data = {
            "deleted_count": result.deleted_count
        }
        data = json.dumps(data)
        return JsonResponse(data, safe=False, status=200)
    
    return JsonResponse({"Error": "Method not allowed"}, status=405)

def LoginView(request):
    if (request.method == "PATCH"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        print(result)
        if (result is None):
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=400)
        return JsonResponse({"Success": True, "Message": "Authorization successful"}, status=200)
    return JsonResponse({"Error": "Method not allowed"}, status=405)

def Authorization(body):
    username = body["Authentication"]["Username"]
    password = body["Authentication"]["Password"]
    hashed_password = Hash_Password(password)
    user = {
        "Username": username,
        "Password": hashed_password
    }
    print(user)
    result = Users.find_one(user)
    return result

def Hash_Password(password):
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password_bytes)
    hashed_password = sha256_hash.hexdigest()
    return hashed_password

        

        