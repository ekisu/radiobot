from . import Base
from sqlalchemy import Column, Integer, Unicode

class Radio(Base):
    __tablename__ = "radio"
    guild_id = Column(Integer, primary_key = True)
    radio_name = Column(Unicode, primary_key = True)
    radio_url = Column(Unicode)

    def __init__(self, guild_id: int, radio_name: str, radio_url: str):
        self.guild_id = guild_id
        self.radio_name = radio_name
        self.radio_url = radio_url
