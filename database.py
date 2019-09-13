import asyncio
import asyncpg
import datetime
class Database:
    def __init__(self, url):
        self.url = url
         
