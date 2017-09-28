import json
from sqlalchemy import orm, Column, Integer, ForeignKey, String, LargeBinary
from cvservice.models import Model

class EventData(Model):
    __tablename__ = 'event_data'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    uri = Column(String(1024))
    # This data will probably be replaced eventually...
    data = Column(LargeBinary(16777215))

    def __init__(self, event_id, uri, data):
        self.event_id = event_id
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