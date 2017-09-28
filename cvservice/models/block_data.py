import json
from sqlalchemy import orm, Column, Integer, ForeignKey, String, LargeBinary
from cvservice.models import Model

class BlockData(Model):
    __tablename__ = 'block_data'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    block_id = Column(Integer, ForeignKey('blocks.id'))
    previous_block_id = Column(Integer, ForeignKey('blocks.id'))
    uri = Column(String(1024))
    # This data will probably be replaced eventually...
    data = Column(LargeBinary(16777215))

    def __init__(self, block_id, previous_block_id, uri, data):
        self.block_id = block_id
        self.previous_block_id = previous_block_id
        self.uri = uri
        self.data = data

        self.json = None


    @orm.reconstructor
    def init_on_load(self):
        self.json = None


    def get_json(self):
        # TODO: Take uri into account.
        if self.json is None:
            if self.data is None:
                self.json = None
            else:
                self.json = json.loads(self.data.decode('ascii'))
        return self.json
