from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine


from dotenv import load_dotenv
import os
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
LocalSession = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass