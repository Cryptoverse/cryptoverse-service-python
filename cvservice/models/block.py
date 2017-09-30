from sqlalchemy import Column, Integer, ForeignKey, String
from cvservice.models import Model

class Block(Model):
    __tablename__ = 'blocks'
    extend_existing = True

    block_id = Column('id', Integer, primary_key=True)
    block_hash = Column('hash', String(64))
    previous_hash = Column(String(64))
    previous_id = Column(Integer, ForeignKey('blocks.id'))
    height = Column(Integer)
    size = Column(Integer)
    version = Column(Integer)
    difficulty = Column(Integer)
    time = Column(Integer)
    interval_id = Column(Integer, ForeignKey('blocks.id'))
    root_id = Column(Integer, ForeignKey('blocks.id'))
    chain = Column(String(64))

    def __init__(self, 
                 block_hash,
                 previous_hash,
                 previous_id,
                 height,
                 size,
                 version,
                 difficulty,
                 time,
                 interval_id,
                 root_id,
                 chain):
        self.block_hash = block_hash
        self.previous_hash = previous_hash
        self.previous_id = previous_id
        self.height = height
        self.size = size
        self.version = version
        self.difficulty = difficulty
        self.time = time
        self.interval_id = interval_id
        self.root_id = root_id
        self.chain = chain