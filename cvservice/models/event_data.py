from sqlalchemy import Column, Integer, ForeignKey, String, LargeBinary
from cvservice.models import Model

class EventData(Model):
    __tablename__ = 'event_data'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('event_pool.id'))
    uri = Column(String(1024))
    data = Column(LargeBinary(16777215))

    def __init__(self, event_id, uri, data):
        self.event_id = event_id
        self.uri = uri
        self.data = data