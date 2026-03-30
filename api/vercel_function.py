import os

from dotenv import load_dotenv

from app import create_app

load_dotenv()
env = os.getenv("VERCEL_ENV", default="production")
app = create_app(env)
