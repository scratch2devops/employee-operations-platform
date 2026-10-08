import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./employees.db"
)

APP_NAME = os.getenv(
    "APP_NAME",
    "Employee Operations Platform"
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)