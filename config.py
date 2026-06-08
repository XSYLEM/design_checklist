import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Telegram user IDs of art directors who can access /board
ART_DIRECTOR_IDS = list(map(int, os.getenv("ART_DIRECTOR_IDS", "").split(","))) if os.getenv("ART_DIRECTOR_IDS") else []
