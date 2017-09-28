from sqlalchemy import Column, Integer, String
from cvservice.models import Model

class Event(Model):
    __tablename__ = 'events'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    key = Column(String(64))
    event_type = Column(String(16))
    size = Column(Integer)
    version = Column(Integer)
    time = Column(Integer)
    
    def __init__(self, 
                 key,
                 event_type,
                 size,
                 version,
                 time):
        self.key = key
        self.event_type = event_type
        self.size = size
        self.version = version
        self.time = time