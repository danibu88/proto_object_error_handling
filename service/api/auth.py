from typing import Optional
from dotenv import load_dotenv
import os


class AuthConfig:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("xxxxxxxx")

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}
