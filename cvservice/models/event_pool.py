from sqlalchemy import Column, Integer, String
from cvservice.models import Model

class EventPool(Model):
    __tablename__ = 'event_pool'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    hash = Column(String(64))
    fleet_hash = Column(String(64))
    time = Column(Integer)
    size = Column(Integer)

    def __init__(self, hash, fleet_hash, time, size):
        self.hash = hash
        self.fleet_hash = fleet_hash
        self.time = time
        self.size = size