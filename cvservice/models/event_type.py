from sqlalchemy import Column, Integer, String
from cvservice.models import Model

class EventType(Model):
    __tablename__ = 'event_types'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    name = Column(String(16))

    def __init__(self, name):
        self.name = name