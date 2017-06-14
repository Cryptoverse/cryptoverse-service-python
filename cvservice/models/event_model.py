from sqlalchemy import Column, Integer, ForeignKey, String
from cvservice.models import Model

class EventModel(Model):
    __tablename__ = 'event_models'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey('event_model_types.id'))
    event_id = Column(Integer, ForeignKey('event_pool.id'))
    usage_id = Column(Integer, ForeignKey('event_usages.id'))
    key = Column(String(64))

    def __init__(self, type_id, event_id, usage_id, key):
        self.type_id = type_id
        self.event_id = event_id
        self.usage_id = usage_id
        self.key = key