from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()  


DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv("DB_PASSWORD"),
    'database': '101_trivia',
}
