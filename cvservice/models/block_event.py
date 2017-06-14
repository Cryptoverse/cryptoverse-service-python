from sqlalchemy import Column, Integer, ForeignKey, String
from cvservice.models import Model

class BlockEvent(Model):
    __tablename__ = 'block_events'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    block_hash = Column(String(64))
    block_id = Column(Integer, ForeignKey('blocks.id'))
    event_hash = Column(String(64))
    event_id = Column(Integer, ForeignKey('event_pool.id'))

    def __init__(self, block_hash, block_id, event_hash, event_id):
        self.block_hash = block_hash
        self.block_id = block_id
        self.event_hash = event_hash
        self.event_id = event_id