"""
mongodb_handler.py

This module connects to a MongoDB database using a URI from environment variables. 
It provides the `connect_db` function to retrieve the client, database, and collection.
"""

import os
import time
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.constants import DB_NAME, COLLECTION_NAME

load_dotenv()
MONGODB_URI = os.environ["MONGODB_URI"]

def connect_db() -> tuple:
    """
    Establishes a connection to the MongoDB database.

    Returns:
        tuple: A tuple containing the MongoDB client, database, and collection objects.
    """
    try:
        client = MongoClient(MONGODB_URI)

        # client.admin.command("ping")
        database = client.get_database(DB_NAME)
        collection = database.get_collection(COLLECTION_NAME)

        time.sleep(1)
        print(f"\n MongoDB connected! Connected Hosts: {client.nodes}")
        # print(f"\n MongoDB connected !! DB HOST: {client.address[0]}")

        # client.close()
        return client, database, collection

    except ConnectionFailure as error:
        raise Exception(f"MONGODB connection FAILED: {error}")
