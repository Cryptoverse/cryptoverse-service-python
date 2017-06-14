from sqlalchemy import Column, Integer, ForeignKey, String
from cvservice.models import Model

class Chain(Model):
    __tablename__ = 'chains'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    block_hash = Column(String(64))
    block_id = Column(Integer, ForeignKey('blocks.id'))
    chain = Column(Integer)

    def __init__(self, block_hash, block_id, chain):
        self.block_hash = block_hash
        self.block_id = block_id
        self.chain = chain