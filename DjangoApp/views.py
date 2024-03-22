import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from bson.json_util import dumps
from bson import ObjectId
import pymongo
import datetime
from dateutil.relativedelta import relativedelta   # pip install python-dateutil to import
import hashlib
# Create your views here.

# Connection to the database & collections
client = pymongo.MongoClient("mongodb+srv://student:student@weatherreadingsdb.hiue8df.mongodb.net/")
db = client["WeatherDataBase"]
Readings = db["Readings"]
Sensors = db["Sensors"]
Users = db["Users"]

# Just an index holder
def index(request):
    return HttpResponse("<h1>Welcome to <u>Weather App API<u>!</h1>")

## ENDPOINT >> UsersView -- for managing users #####
    # /users > POST
def UsersView(request):
    if (request.method == "POST"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)

        # Allow access only if role is Admin or Teacher
        if role != "Admin" and role != "Teacher" :
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        
        # Return error message if user already exists
        if (Users.find_one({"Username": body["Username"]}) is not None):
            return JsonResponse({"Success": False, "Message": "User already exists"}, status=404)
        
        # Collate new user details from input data and calculate lastlogin datetime
        ## NOTE: Should check for missing information here and provide a useful error message if missing
                # i.e. Mandatory fields = Username, Password, Role (FName, LName optional?)
        newUser = {
            "Username": body["Username"],
            "Password": Hash_Password(body["Password"]),
            "FName": body["FName"],
            "LName": body["LName"],
            "Role": body["Role"],
            "LastLogin": datetime.datetime.now(tz=datetime.timezone.utc),
            "Token": None,
        }

        # Insert the new user
        result = Users.insert_one(newUser)

        # Return the ID of the new user
        data = {
            "Inserted_id": str(result.inserted_id)
        }
        return JsonResponse(data, status=200)
    
    # /users > DELETE
    if (request.method == "DELETE"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)

        id = body.get("_id")
        objId = ObjectId(id)

        roleForDelete = body.get("Role")

        # convert date time strings (in format YYYY-MM-DD HH:MM:SS) to datetime object
        startDate = datetime.datetime.strptime(body.get('StartDate'),'%Y-%m-%d')
        endDate = datetime.datetime.strptime(body.get('EndDate'),'%Y-%m-%d')

        # Allow access only if role is Admin or Teacher
        if role != "Admin" and role != "Teacher" :
            return JsonResponse({"Success": False, "Role": role, "Message": "Authorisation failed"}, status=401)
        
        # Search for User by ID
        # Return error message if the user ID does not exist (in request details)
        if id:
            # Search for the username in the collection
            idToDelete = {"_id": objId}
        
            # If ID is found, delete the user and return confirmation
            if idToDelete:
                result = Users.delete_one(idToDelete)
                return JsonResponse({"Success": True, "Role": roleForDelete, 
                                     "Message": f"User with Id: {idToDelete} deleted sucessfully"}, status=200)

        # Search for multiple users by Role and a date range for LastLogin     
        if roleForDelete and startDate and endDate:
            print("Searching for users")
            print(f"Role: {roleForDelete}, StartDate: {startDate}, EndDate: {endDate}")
            # Data filter for role and date range
            query = {
                "Role": roleForDelete,
                "LastLogin": {"$gte": startDate, "$lte": endDate}
            }
            print(query)

            # Query the Users collection
            foundUsers = Users.find(query)
            print(foundUsers)

            # List to store IDs of users to delete
            idsToDelete = [user["_id"] for user in foundUsers]

            print(idsToDelete)

            if idsToDelete:
                result = Users.delete_many({"_id": {"$in": idsToDelete}})
                return JsonResponse({"Success": True, "Role": role, 
                                        "Message": f"User with Id: {result.deleted_count} deleted sucessfully"}, status=200)
            
        # User/s could not be found, return error message
        return JsonResponse({"Success": False, "Message": "Failed to delete user/s"}, status=403)
          
    # /users > PUT
    if (request.method == "PUT"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)

        if role != "Admin" and role != "Teacher" :
            return JsonResponse({"Success": False, "Role" : role, "Message": "Authorisation failed"}, status=401)
        
        if "Username" not in body:
            return JsonResponse({"Success": False, "Role" : role, "Message": "Username not provided"}, status=400)
        
        user_query = {
            "Username": body["Username"]
        }
        existing_user = Users.find_one(user_query)
        if existing_user is None:
            return JsonResponse({"Success": False, "Role" : role, "Message": "User not found"}, status=404)
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
            return JsonResponse({"Success": True, "Role" : role,
                                   "Message": "User details updated successfully"}, status=200)
        else:
            return JsonResponse({"Success": False, "Message": "Failed to update user details"}, status=400)
      
    # /users > PATCH
    if (request.method == "PATCH"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)

        startDate = body.get('StartDate')
        endDate = body.get('EndDate')
        currentRole = body.get("CurrentRole")
        changedRole = body.get("ChangedRole")

        # Read in Start date and End date
        if startDate and endDate:
            dateRange = True
            # convert date time strings (in format YYYY-MM-DD HH:MM:SS) to datetime object
            startDate = datetime.datetime.strptime(startDate,'%Y-%m-%d')
            endDate = datetime.datetime.strptime(endDate,'%Y-%m-%d')
        
        if role != "Admin":
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)

        # Create a temporary collection to hold the extracted data
        temp_collection = {}

        # Create a list from Users collection
        # Query the collection and convert the cursor to a list
        cursor = Users.find()
        usersList = list(cursor)      

        # Iterate over the users and extract the data
        for user in usersList:
            object_id = user["_id"]
            role = user["Role"]
            
            # Extract the timestamp from the ObjectId
            timestamp = object_id.generation_time.timestamp()

            # Convert the timestamp to a datetime object
            date_created = datetime.datetime.fromtimestamp(timestamp)

            # Add the extracted data to the temporary collection
            temp_collection[object_id] = {"role": role, "date_created": date_created}

        # Counter for users that match search
        changeCount = 0

        # Search for users based on the extracted date
        for object_id, data in temp_collection.items():
            if startDate <= data["date_created"] <= endDate and data["role"] == currentRole:
                print(f"User ID: {object_id}, Role: {data['role']}, Date Created: {data['date_created']}")

                update_query = {"$set": {"Role": changedRole}}
                result = Users.update_one({"_id": object_id}, update_query)
        
                if result.modified_count > 0:
                    changeCount += 1

        if changeCount > 0:
            return JsonResponse({"Success": True, "Message": f"{changeCount} user roles updated successfully"}, status=200)
        else:
            return JsonResponse({"Success": False, "Message": "Failed to update user roles"}, status=400) 
    # End /users > PATCH
      
        
    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)


## ENDPOINT >> /readings -- for managing weather readings #####
def ReadingsView (request):
    # /readings GET
    if(request.method == "GET"):

        # Read in valid parameters from URL (DeviceName, DateTime, FirstTemp, SecondTemp)
        deviceName = request.GET.get('DeviceName')
        readingDateTime = request.GET.get('DateTime')
        firstTemp = float(request.GET.get('FirstTemp'))
        secondTemp = float(request.GET.get('SecondTemp'))

        # Get request to obtain specific reading details based on inputs > DeviceName, DateTime
        if deviceName and readingDateTime:
            # convert date time string (in format YYYY-MM-DD HH:MM:SS) to datetime object
            convertedDateTime = datetime.datetime.strptime(readingDateTime,'%Y-%m-%d %H:%M:%S')

            reading = Readings.find_one({"Device Name": deviceName, "Time": convertedDateTime})

            # Return temperature, atmospheric pressure, radiation & precipitation (if found)
            if reading:
                returnData = {
                    "Temperature(°C)": reading.get("Temperature (°C)", None),
                    "Atmospheric Pressure (kPa)": reading.get("Atmospheric Pressure (kPa)", None),
                    "Solar Radiation (W/m2)": reading.get("Solar Radiation (W/m2)", None),
                    "Precipitation mm/h": reading.get("Precipitation mm/h", None)
                }

        # Get request to obtain a range of readings based on inputs > FirstTemp, SecondTemp
        # Create a query that includes an index key:( PETER wants:(get 2 different temp and return between temprature)
        # /readings/?firstTemp=23.00&secondTemp=23.07  
        if firstTemp and secondTemp:
            # Construct query to find readings within the temperature range
            query = {'Temperature (°C)': {'$gte': firstTemp, '$lte': secondTemp}}
        
            # Find readings matching the temperature range and sort them by temperature in descending order
            result = Readings.find(query).sort('Temperature (°C)', -1).limit(10)

            list_cur = list(result)
            returnData = dumps(list_cur)
        
        return JsonResponse(returnData, safe=False)

    # /readings POST NOTE *********Currently a work in progress
    if(request.method == "POST"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)
        deviceName = body.get('Device Name')
        readings = body.get('Readings', [])

        # Print extracted readings
        print(readings)

        # Initialise messages and counters
        # Error for skipped records
        errMessage = ""
        errCount = 0
        # Count the number of weather readings to be added (this will not include duplicates)
        numRecords = 0

        if role != "Admin" and role != "Teacher" and role != "Sensor":
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)

        # Return error message if Device does not exist
        if (Sensors.find_one({"DeviceName": deviceName}) is None):
            return JsonResponse({"Success": False, "Message": "Device does not exist"}, status=404)
       
        # Use device name to get latitude and longitude
        latitude_longitude = GetLatitudeLongitude(deviceName)

        # List to store all new readings
        newReadingsList = []

        for data in readings:
            # Check if reading already exists using Device Name and Time
            if (Readings.find_one({"Device Name": deviceName,"Time": data["Time"]}) is not None):
                errCount += 1
            else:
                convertedDateTime = datetime.datetime.strptime(data.get("Time"),'%Y-%m-%d %H:%M:%S')
                newReading = {
                        "Device Name": deviceName,
                        "Precipitation mm/h": data.get("Precipitation mm/h"),
                        "Time": convertedDateTime,
                        "Latitude": latitude_longitude["Latitude"],
                        "Longitude": latitude_longitude["Longitude"],
                        "Temperature (°C)": data.get("Temperature (°C)"),
                        "Atmospheric Pressure (kPa)": data.get("Atmospheric Pressure (kPa)"),
                        "Max Wind Speed (m/s)": data.get("Max Wind Speed (m/s)"),
                        "Solar Radiation (W/m2)": data.get("Solar Radiation (W/m2)"),
                        "Vapor Pressure (kPa)": data.get("Vapor Pressure (kPa)"),
                        "Humidity (%)": data.get("Humidity (%)"),
                        "Wind Direction (°)": data.get("Wind Direction (°)")
                    }
                newReadingsList.append(newReading)
                #numRecords += 1  
            #print("Error count" + errCount)
            #print("New readings" + str(numRecords))

        numRecords = len(newReadingsList)
        print(numRecords)

        if numRecords == 1:
            result = Readings.insert_one(newReadingsList)
            
        elif  numRecords > 1:
            result = Readings.insert_many(newReadingsList) 
                
        else:
            return JsonResponse({"status":"error", "message":"Invalid request"}, status=400)

        print(result)

        if errCount > 1:
            errMessage = str(errCount) + " duplicate reading not added."

        returnMessage = str(numRecords) + " readings added successfully." + errMessage 

        return JsonResponse({"status": "success", "message": returnMessage}, status=200)

    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)

## ENDPOINT >> /sensors -- for managing sensors ##
# /sensors > POST
def SensorsView(request):
    # /sensors > GET NOTE for use in dev testing only > Find unique entries for 'Device Name' (under readings)
    if (request.method == "GET"):
        unique_device_names = Readings.distinct('Device Name')

        return JsonResponse(unique_device_names, safe=False)

    # /sensors > POST
    if (request.method == "POST"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)

        # Allow access only if role is Admin
        if role != "Admin" :
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        
        # Return error message if sensor already exists
        if (Users.find_one({"DeviceName": body["DeviceName"]}) is not None):
            return JsonResponse({"Success": False, "Message": "Sensor already exists"}, status=404)
        
        # Collate new sensor details from input data
        ## NOTE: Should check for missing information here and provide a useful error message if missing
        newSensor = {
            "DeviceName": body["DeviceName"],
            "Latitude": body["Latitude"],
            "Longitude": body["Longitude"],
        }

        # Insert the new sensor
        result = Sensors.insert_one(newSensor)

        # Return the ID of the new sensor
        data = {
            "Inserted_id": str(result.inserted_id)
        }
        return JsonResponse(data, status=200)
    
    # /sensors > DELETE
    if (request.method == "DELETE"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)

        # Allow access only if role is Admin
        if role != "Admin":
            return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=401)
        
        # Return error message if the username does not exist (in request details)
        if "DeviceName" not in body:
            return JsonResponse({"Success": False, "Message": "DeviceName not provided"}, status=400)
        
        # Search for the username in the collection
        sensorToDelete = {"DeviceName": body["DeviceName"]}

        # If username is found, delete the user and return confirmation
        if sensorToDelete:
            result = Sensors.delete_one(sensorToDelete)
            data = {"deleted_count": result.deleted_count}
            return JsonResponse(data, status=200)
        
        # Username is not found, return error message
        return JsonResponse({"Success": False, "Message": "Couldn't Find DeviceName"}, status=403)

    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)


## ENDPOINT >> analysis -- NOT IN USE  #####
# /analysis > POST
def AnalysisView(request):

    return ""


## ENDPOINT >> /analysis/max -- for calculating max value of Temperature or Precipitation of readings #####
def AnalysisMaxView(request):
    # examples of request parameters
    # /analysis/max?Find=Temperature&StartDate=2020-01-01&EndDate=2021-04-01
    # /analysis/max?Find=Precipitation&DeviceName=Woodford_Sensor&StartDate=2020-01-01&EndDate=2020-04-01
    # /analysis/max?Find=Precipitation&DeviceName=Woodford_Sensor&StartDate=2020-01-01&EndDate=2021-04-01
    # /analysis/max GET
    if(request.method == "GET"):

        findField = request.GET.get('Find')
        deviceName = request.GET.get('DeviceName')

        currentDate = datetime.datetime.now()
        dateRange = None

        # Calculate dates for a five month range (prior to now)
        # Start date and End date
        if request.GET.get('StartDate') and request.GET.get('EndDate'):
            dateRange = True
            # convert date time strings (in format YYYY-MM-DD HH:MM:SS) to datetime object
            startDate = datetime.datetime.strptime(request.GET.get('StartDate'),'%Y-%m-%d')
            endDate = datetime.datetime.strptime(request.GET.get('EndDate'),'%Y-%m-%d')

        # Return error for bad request if only one of start or end date is included
        elif request.GET.get('StartDate') or request.GET.get('EndDate'):
            return JsonResponse({"Error": "Paramaters need to include a start and end date"}, status=400)
        
        else:
            dateRange = False
            # https://www.geeksforgeeks.org/how-to-add-and-subtract-days-using-datetime-in-python/
            startDate = currentDate - relativedelta(months = 5)
            endDate = currentDate
        
        # Create the data filters
        # Data filter including Sensor Name
        if deviceName:
            dateFilter = {
                "Device Name": deviceName,
                "Time": {"$gte": startDate, "$lte": endDate}
            }
        # Data filter excluding Sensor Name
        else:
            dateFilter = {
                "Time": {"$gte": startDate, "$lte": endDate}
            }

        # Query the Readings collection
        maximumReading = Readings.find(dateFilter).sort('Precipitation mm/h', -1).limit(1)

        # Initialise returnData and errorMessage to None
        returnData = None

        # Return temperature, atmospheric pressure, radiation & precipitation (if found)
        if maximumReading:
            for result in maximumReading:
                if findField == "Precipitation":
                    returnData = {
                        "Device Name": result.get("Device Name", None),
                        "Time": result.get("Time", None),
                        "Precipitation mm/h": result.get("Precipitation mm/h", None)
                    }

                elif findField == "Temperature":
                    returnData = {
                        "Device Name": result.get("Device Name", None),
                        "Time": result.get("Time", None),
                        "Temperature (°C)": result.get("Temperature (°C)", None)     
                    }

        if returnData is not None:
            return JsonResponse(returnData)
        
        # No Content
        if dateRange == True:
            return  JsonResponse({"Success": False, "Message": "No records found within the specified date range"}, status=204)
        elif dateRange == False:               
            return JsonResponse({"Success": False, "Message": "No records found within last 5 months"}, status=204)

    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)        
    
# ENDPOINT >> /users/role -- use for testing > Returns the role of the user logging in
def UsersRoleView(request):
    # /users/role > PATCH
    if (request.method == "PATCH"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorization(body)

        if role:
            return JsonResponse({"Success": True, "Message": "Authorisation successful", "Role": role}, status=200)

        return JsonResponse({"Success": False, "Message": "Authorisation failed"}, status=400)     

    # Returns error: method not allowed for any other methods        
    return JsonResponse({"Error": "Method not allowed"}, status=405)


## ENDPOINT >> /login -- for managing user login #####
# This is the login endpoint, right now it works like checking if the account is legit
def LoginView(request):
    # /login PATCH
    if (request.method == "PATCH"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorization(body)
        print(result)
        if result:
            return JsonResponse({"Success": True, "Message": "Authorization successful"}, status=200)
        return JsonResponse({"Success": False, "Message": "Authorization failed"}, status=400)

    # Returns error: method not allowed for any other methods        
    return JsonResponse({"Error": "Method not allowed"}, status=405)

## FUNCTIONS #########################################################################################
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
    # Return role from the user (if found)
    if result:
        # Update the last login date for the user
        update_data = {
            "LastLogin": datetime.datetime.now(datetime.timezone.utc)
        }
        Users.update_one(user, {"$set": update_data})
        #role = {
        #    "Role": result.get("Role", None),
        #}
        # Save the role > return this
        role = result.get("Role", None)
        return role
    return None

# Hash password function
def Hash_Password(password):
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password_bytes)
    hashed_password = sha256_hash.hexdigest()
    return hashed_password

# Get latitude and longitude for a Sensor
def GetLatitudeLongitude(deviceName):
    result = Sensors.find_one({"DeviceName": deviceName})

    # Return latitude and longitude (if found)
    if result:
        latitude_longitude = {
            "Latitude": result.get("Latitude", None),
            "Longitude": result.get("Longitude", None)
        }
        return latitude_longitude
    return None