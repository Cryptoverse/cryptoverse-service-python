from sqlalchemy import Column, Integer, ForeignKey, String, LargeBinary
from cvservice.models import Model

class BlockData(Model):
    __tablename__ = 'block_data'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    block_id = Column(Integer, ForeignKey('blocks.id'))
    uri = Column(String(1024))
    data = Column(LargeBinary(16777215))

    def __init__(self, block_id, uri, data):
        self.block_id = block_id
        self.uri = uri
        self.data = data