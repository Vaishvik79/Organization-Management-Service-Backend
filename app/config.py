import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Flask core secret
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Mongo
    MONGO_URI = os.getenv("MONGO_URI")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"
