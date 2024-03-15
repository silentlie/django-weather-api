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
# Just a index holder
def index(request):
    return HttpResponse("<h1>Welcome to <u>Weather App API<u>!</h1>")
# UsersView endpoint for managing users
def UsersView(request):
    if (request.method == "POST"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        if (result is None or result["Role"] != "Admin"):
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        if (Users.find_one({"Username": body["Username"]}) is not None):
            return JsonResponse({"Success": False, "Message": "Couldn't Find Username"}, status=404)
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
        return JsonResponse(data, status=200)
    if (request.method == "DELETE"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        if (result is None or result["Role"] != "Admin"):
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        if "Username" not in body:
            return JsonResponse({"Success": False, "Message": "Username not provided"}, status=400)
        userToDelete = {
            "Username": body["Username"]
        }
        if (Users.find_one(userToDelete) is None):
            return JsonResponse({"Success": False, "Message": "Couldn't Find Username"}, status=403)
        result = Users.delete_one(userToDelete)
        data = {
            "deleted_count": result.deleted_count
        }
        return JsonResponse(data, status=200)
    if (request.method == "PUT"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        if result is None or result["Role"] != "Admin":
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        if "Username" not in body:
            return JsonResponse({"Success": False, "Message": "Username not provided"}, status=400)
        user_query = {
            "Username": body["Username"]
        }
        existing_user = Users.find_one(user_query)
        if existing_user is None:
            return JsonResponse({"Success": False, "Message": "User not found"}, status=404)
        update_data = {}
        if "Password" in body:
            update_data["Password"] = Hash_Password(body["Password"])
        if "FName" in body:
            update_data["FName"] = body["FName"]
        if "LName" in body:
            update_data["LName"] = body["LName"]
        if "Role" in body:
            update_data["Role"] = body["Role"]
        update_data["LastLogin"] = datetime.datetime.now(datetime.timezone.utc)
        result = Users.update_one(user_query, {"$set": update_data})
        if result.modified_count > 0:
            return JsonResponse({"Success": True, "Message": "User details updated successfully"}, status=200)
        else:
            return JsonResponse({"Success": False, "Message": "Failed to update user details"}, status=400)
    return JsonResponse({"Error": "Method not allowed"}, status=405)
# This is the login endpoint, right now it works like checking if the account is legit
def LoginView(request):
    if (request.method == "PATCH"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        print(result)
        if (result is None):
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=400)
        return JsonResponse({"Success": True, "Message": "Authorization successful"}, status=200)
    return JsonResponse({"Error": "Method not allowed"}, status=405)
# Check point function of every request for authorization
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
    update_data = {
        "LastLogin": datetime.datetime.now(datetime.timezone.utc)
    }
    Users.update_one(user, {"$set": update_data})
    # Should return role instead
    return result
# Hash password function
def Hash_Password(password):
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password_bytes)
    hashed_password = sha256_hash.hexdigest()
    return hashed_password