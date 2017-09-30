from sqlalchemy import Column, Integer, String
from cvservice.models import Model

class Event(Model):
    __tablename__ = 'events'
    extend_existing = True

    event_id = Column('id', Integer, primary_key=True)
    event_hash = Column('hash', String(64))
    key = Column(String(64))
    event_type = Column(String(16))
    size = Column(Integer)
    version = Column(Integer)
    received_time = Column(Integer)
    confirmation_count = Column(Integer)
    
    def __init__(self,
                 event_hash,
                 key,
                 event_type,
                 size,
                 version,
                 received_time,
                 confirmation_count):
        self.event_hash = event_hash
        self.key = key
        self.event_type = event_type
        self.size = size
        self.version = version
        self.received_time = received_time
        self.confirmation_count = confirmation_count