import pymongo
from django.db import models

# Connection to the database & collections
client = pymongo.MongoClient("mongodb+srv://student:student@weatherreadingsdb.hiue8df.mongodb.net/")
db = client["WeatherDataBase"]
Readings = db["Readings"]
Sensors = db["Sensors"]
Users = db["Users"]
    
def findOneFunction(collection, query, projection=None):
    if projection is None:
        result = getCollection(collection).find_one(query)

    result = getCollection(collection).find_one(query, projection)
    return result

def findManyFunction(collection, query, sortField=None, sortKey=1, findLimit=None):
    if sortField is None and findLimit is None:
        result = getCollection(collection).find(query)
    elif sortField is None:
        result = getCollection(collection).find(query).limit(findLimit)
    elif findLimit is None:
        result = getCollection(collection).find(query).sort(sortField, sortKey)
    result = getCollection(collection).find(query).sort(sortField, sortKey).limit(findLimit)
    return result

def insertOneFunction(collection, query):
    result = getCollection(collection).insert_one(query)
    return result

def insertManyFunction(collection, query):
    result = getCollection(collection).insert_many(query)
    return result

def updateOneFunction(collection, query, updateData):
    result = getCollection(collection).update_one(query, updateData)
    return result

def updateManyFunction(collection, query, updateData):
    result = getCollection(collection).update_many(query, updateData)
    return result

def replaceOneFunction(collection, query, replaceData):
    result = getCollection(collection).replace_one(query, replaceData)
    return result

def deleteOneFunction(collection, query):
    result = getCollection(collection).delete_one(query)
    return result

def deleteManyFunction(collection, query):
    result = getCollection(collection).delete_many(query)
    return result

def getCollection(collection):
    if collection == 'readings':
        return Readings
    elif collection == 'users':
        return Users
    elif collection == 'sensors':
        return Sensors
    



# Create your models here.


    