import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from bson.json_util import dumps
from bson.objectid import ObjectId
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

# def lambda_handler(event, context):
#     return {
#         'statusCode': 200,
#         'headers': {
#             'Access-Control-Allow-Headers': 'Content-Type',
#             'Access-Control-Allow-Origin': http//:127.0.0.1:8000
#             'Access-Control-Allow-Methods': 'OPTIONS, GET, POST, PUT, PATCH, DELETE'
#         },
#         'body': json.dumps('Hello from Lambda!')
#     }

## ENDPOINT >> UsersView -- for managing users #####
def UsersView(request):
    ## Load body
    body = json.loads(request.body.decode("utf-8"))
    role = Authorisation(body)

    # /users > Authentication and authorisation ##
    # Allow access to user endpoint requests only if role is Admin or Teacher
    if role is None:
        return JsonResponse({"Success": False, "Message": "Authentication failed"}, status=401)
    if role != "Admin" and role != "Teacher" :
        return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Authorisation failed"}, status=401)
    
    # /users > POST
    if (request.method == "POST"):        
        ## Get data from request ##
        username = body.get("Username")
        password = Hash_Password(body.get("Password"))
        userRole = body.get("Role")
        fName = body.get("FName", None)
        lName = body.get("LName", None)
        token = body.get("Token", None)

        ## Process ##
        # Return error message if user already exists
        if (Users.find_one({"Username": username}) is not None):
            return JsonResponse({"Success": False, "Authorisation": "Successful", "Authorisation role": role,
                                 "Message": "User already exists"}, status=409)
        
        # Check that password and userRole have been included in the body, then add user
        if password and userRole:
        # Collate new user details from input data and calculate lastlogin datetime
        # Collate new user details from input data and calculate lastlogin datetime
        ## NOTE: Should check for missing information here and provide a useful error message if missing
                # i.e. Mandatory fields = Username, Password, Role (FName, LName optional?)
            # Collate new user details from input data and calculate lastlogin datetime
        ## NOTE: Should check for missing information here and provide a useful error message if missing
                # i.e. Mandatory fields = Username, Password, Role (FName, LName optional?)
            newUser = {
                "Username": username,
                "Password": password,
                "FName": fName,
                "LName": lName,
                "Role": userRole,
                "LastLogin": datetime.datetime.now(tz=datetime.timezone.utc),
                "Token": token,
            }

            # Insert the new user
            result = Users.insert_one(newUser)

            # Get the ID of the new user and return success message
            newID = {"Inserted_id": str(result.inserted_id)}
            return JsonResponse({"Success": True, "Authorisation role": role, "Message": f"New user, {newID}, sucessfully created."}, status=200)
        
        # Response for malformed request
        return JsonResponse({"Success": False, "Authorisation": "Successful", "Authorisation role": role, 
                                        "Message": "Request does not contain required information"}, status=400)
    ## End /users > POST
    
    # /users > DELETE
    if (request.method == "DELETE"):        
        ## Get data from request ##
        # For deleting a single user:
        # Get ID from URL paramaters OR username from body
        id = body.get("ID")
        username = body.get("Username")

        # For deleting multiple users of a particular role, with LastLogin within a specified date range
        roleForDelete = body.get("Role")
        startDate = body.get('StartDate')
        endDate = body.get('EndDate')

        ## Process ##
        # Delete many
        # Search for multiple users by Role and a date range for LastLogin     
        if roleForDelete and startDate and endDate:
            # convert date time strings (in format YYYY-MM-DD HH:MM:SS) to datetime object
            startDate = datetime.datetime.strptime(body.get('StartDate'),'%Y-%m-%d')
            endDate = datetime.datetime.strptime(body.get('EndDate'),'%Y-%m-%d')

            # Query for role and date range
            query = {
                "Role": roleForDelete,
                "LastLogin": {"$gte": startDate, "$lte": endDate}
            }

            result = Users.delete_many(query)

            if result.deleted_count > 0:
                return JsonResponse({"Success": True, "Authorisation role": role, 
                                        "Message": f"{result.deleted_count} users deleted sucessfully"}, status=200)
            else:
                return JsonResponse({"Success": False, "Authorisation role": role, 
                                        "Message": "No users found for the given criteria"}, status=404)
        
        # Delete one
        # Delete single user (by ID or Username - depending on which is provided)
        if id or username:

            print(f"ID {id} and username {username}")
            query = ""
            
            if id:
                # Search for the user by ID
                query = {"_id": ObjectId(id)}

            elif username:
                # Search for the user by Username
                query = {"Username": username}
            

            result = Users.delete_one(query)

            if result.deleted_count > 0:
                return JsonResponse({"Success": True, "Authorisation role": role, 
                                        "Message": f"User deleted sucessfully"}, status=200)
            else:
                return JsonResponse({"Success": False, "Authorisation role": role, 
                                        "Message": "User not found"}, status=404)

        # Response for malformed request
        return JsonResponse({"Success": False, "Authorisation role": role, 
                                "Message": "Request does not contain required information"}, status=400)
    ## End /users > DELETE

    # /users > PUT
    if (request.method == "PUT"):
        # Check that username (for the user to be updated) has been included in the request      
        if "Username" not in body:
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Username not provided"}, status=400)
        
        # Search for the user in the collection
        query = {"Username": body["Username"]}
        existing_user = Users.find_one(query)

        # If the use is not found return an error
        if existing_user is None:
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "User not found"}, status=404)
        
        #Update the user data
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

        result = Users.update_one(query, {"$set": update_data})
        if result.modified_count > 0:
            return JsonResponse({"Success": True, "Authorisation role": role,
                                   "Message": "User details updated successfully"}, status=200)
        else:
            return JsonResponse({"Success": False, "Message": "Failed to update user details"}, status=400)
    ## End /users > PUT
      
    # /users > PATCH
    if (request.method == "PATCH"):

        # Override general authorisation to limit access for this method to Admin only
        if role != "Admin":
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Authorisation failed"}, status=401)
        
        # Read in data from request
        startDate = body.get('StartDate')
        endDate = body.get('EndDate')
        currentRole = body.get("CurrentRole")
        changedRole = body.get("ChangedRole")

        start_id = None
        end_id = None
        
        if startDate and endDate:
            # convert date time strings (in format YYYY-MM-DD HH:MM:SS) to datetime object
            startDate = datetime.datetime.strptime(startDate,'%Y-%m-%d')
            print(startDate)
            endDate = datetime.datetime.strptime(endDate,'%Y-%m-%d')
            print(endDate)
            start_id = ObjectId.from_datetime(startDate)
            print(start_id)
            end_id = ObjectId.from_datetime(endDate)
            print(end_id)
        
        query = { "_id": {"$gte": start_id, "$lte": end_id}, "Role": currentRole}
        
        result = Users.update_many(query,{"$set": {"Role": changedRole}})
        changeCount = result.modified_count

        if result.modified_count > 0:
            return JsonResponse({"Success": True, "Authorisation role": role, "Message": f"{changeCount} user roles updated successfully"}, status=200)
        else:
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "No users found for the given criteria"}, status=400)
    # End /users > PATCH

    
    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)
# End ENDPOINT /users



########### ADD IN AN API REQUEST USING OPTIONS ################################3



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

    # /readings POST
    if(request.method == "POST"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorisation(body)
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
        if role is None:
            return JsonResponse({"Success": False, "Message": "Authentication failed"}, status=401)
        if role != "Admin" and role != "Teacher" and role != "Sensor":
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Authorisation failed"}, status=401)

        # Return error message if Device does not exist
        if (Sensors.find_one({"DeviceName": deviceName}) is None):
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Sensor(device) does not exist"}, status=404)
       
        # Use device name to get latitude and longitude
        latitude_longitude = GetLatitudeLongitude(deviceName)
        if latitude_longitude is None:
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Sensor location could not be found"}, status=404)
        
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

        numRecords = len(newReadingsList)
        print(numRecords)

        if numRecords == 1:
            result = Readings.insert_one(newReadingsList)
            
        elif  numRecords > 1:
            result = Readings.insert_many(newReadingsList) 
                
        else:
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Invalid request"}, status=400)

        print(result)

        if errCount > 1:
            errMessage = f" {errCount} duplicate readings not added."

        returnMessage = f"{numRecords} readings added successfully.{errMessage}" 

        return JsonResponse({"Success": True, "Authorisation role": role, "Message": returnMessage}, status=200)
    ## End /readings POST

    # /readings PATCH
    if(request.method == "PATCH"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorisation(body)
        
        id = body.get("ReadingID")
        new_precipitation = body.get("Precipitation")

        if role is None:
            return JsonResponse({"Success": False, "Message": "Authentication failed"}, status=401)
        # Allow access only if role is Admin or Teacher
        if role != "Admin" and role != "Teacher" :
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Authorisation failed"}, status=401)
        
        try:
            objId = ObjectId(id)
            # Find the existing reading
            existing_reading = Readings.find_one({"_id": objId})

            if existing_reading:
                existing_reading["Precipitation mm/h"] = new_precipitation
                Readings.update_one({"_id": objId}, {"$set": existing_reading})
                return JsonResponse({"Success": True, "Authorisation role": role, "Message": "Reading updated successfully"})
        
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Reading not found"}, status=404)

        except Exception as e:
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": str(e)}, status=400)
        # END /readings PATCH

    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)
## End ENDPOINT >> /readings


## ENDPOINT >> /sensors -- for managing sensors ##
# /sensors POST
def SensorsView(request):
    # /sensors > POST
    if (request.method == "POST"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorisation(body)

        if role is None:
            return JsonResponse({"Success": False, "Message": "Authentication failed"}, status=401)
        # Allow access only if role is Admin
        if role != "Admin" :
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Authorisation failed"}, status=401)
        
        # Return error message if sensor already exists
        if (Users.find_one({"DeviceName": body["DeviceName"]}) is not None):
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Sensor already exists"}, status=404)
        
        # Collate new sensor details from input data
        ## NOTE: Should check for missing information here and provide a useful error message if missing
        newSensor = {
            "DeviceName": body["DeviceName"],
            "Latitude": body["Latitude"],
            "Longitude": body["Longitude"],
        }

        # Insert the new sensor
        result = Sensors.insert_one(newSensor)

        return JsonResponse({"Success": True, "Authorisation role": role, "Message": f"Sensor {result.inserted_id} successfully added"}, status=404)
    ## End /sensors POST
    
    # /sensors > DELETE
    if (request.method == "DELETE"):
        body = json.loads(request.body.decode("utf-8"))
        role = Authorisation(body)

        if role is None:
            return JsonResponse({"Success": False, "Message": "Authentication failed"}, status=401)
        # Allow access only if role is Admin
        if role != "Admin":
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Authorisation failed"}, status=401)
        
        # Return error message if the username does not exist (in request details)
        if "DeviceName" not in body:
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "DeviceName not provided"}, status=400)
        
        # Search for the username in the collection
        sensorToDelete = {"DeviceName": body["DeviceName"]}

        result = Sensors.delete_one(sensorToDelete)

        if result.deleted_count > 0:    
            return JsonResponse({"Success": True, "Authorisation role": role, "Message": f"Sensor {result.deleted_count} successfully deleted"}, status=200)
        else:
            # Username is not found, return error message
            return JsonResponse({"Success": False, "Authorisation role": role, "Message": "Couldn't Find Sensor (Device Name)"}, status=403)
    ## End /sensors DELETE

    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)


## ENDPOINT >> analysis -- NOT IN USE  #####
# Uses AnalysisView


## ENDPOINT >> /analysis/max -- for calculating max value of Temperature or Precipitation of readings #####
def AnalysisMaxView(request):

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

        print(dateFilter)

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
            return JsonResponse(returnData, status=200)
        
        # No Content
        if dateRange == True:
            return  JsonResponse({"Success": False, "Message": "No records found within the specified date range"}, status=204)
        elif dateRange == False:               
            return JsonResponse({"Success": False, "Message": "No records found within last 5 months"}, status=204)
    ## End /analysis/max GET

    # Returns error: method not allowed for any other methods
    return JsonResponse({"Error": "Method not allowed"}, status=405)        


## ENDPOINT >> /login -- for managing user login #####
# This is the login endpoint, right now it works like checking if the account is legit
def LoginView(request):
    # /login PATCH
    if (request.method == "PATCH"):
        body = json.loads(request.body.decode("utf-8"))
        result = Authorisation(body)
        print(result)

        if result:
            return JsonResponse({"Success": True, "Message": "Authentication successful"}, status=200)
        return JsonResponse({"Success": False, "Message": "Authentication failed"}, status=400)
    ## End /login PATCH

    # Returns error: method not allowed for any other methods        
    return JsonResponse({"Error": "Method not allowed"}, status=405)

## FUNCTIONS #########################################################################################
# Check point function of every request for Authorisation
def Authorisation(body):
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
## End Authorisation function

# Hash password function
def Hash_Password(password):
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password_bytes)
    hashed_password = sha256_hash.hexdigest()
    return hashed_password
## End Hash password function

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
## End Get latitude and longitude for a Sensor function