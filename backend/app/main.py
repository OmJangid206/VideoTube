"""
main.py: Entry point for running the FastAPI application.

- Loads environment variables from a `.env` file.
- Establishes a MongoDB connection using `connect_db`.
- Starts the server at `http://127.0.0.1:8000/api/v1` using Uvicorn.

Ensure a `.env` file with the necessary configurations is present.
"""

import uvicorn

from dotenv import load_dotenv
from app.db.mongodb_handler import connect_db
from app.app import app

load_dotenv()
client, database, collection = connect_db()

print("🚀 Server is running at http://127.0.0.1:8000/api/v1")

uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
