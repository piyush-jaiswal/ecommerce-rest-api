import os

from app import create_app

# load_env already called by importing create_app (by config.py)
env = os.getenv("VERCEL_ENV", default="production")
app = create_app(env)
