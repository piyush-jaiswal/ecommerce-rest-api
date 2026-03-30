import os

from app import create_app

# dotenv.load_dotenv() already called by importing create_app (via config.py)
env = os.getenv("VERCEL_ENV", default="production")
app = create_app(env)
