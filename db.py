import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client["memorylog"]
users_collection = db["users"]
history_collection = db["history"]
location_collection = db["locations"]
