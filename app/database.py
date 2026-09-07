import os

import pymongo
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "rag_users")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DATABASE]

users_collection = db["users"]
documents_collection = db["documents"]
users_collection.create_index("email", unique=True)