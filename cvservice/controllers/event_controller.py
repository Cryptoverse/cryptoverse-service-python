import json
import traceback
from cvservice import util
from cvservice import validate
from cvservice.views.event_api import EventApi
from cvservice.models.event import Event
from cvservice.models.event_data import EventData

class EventController(object):

    def __init__(self, app):
        self.database = app.database
        self.rules = app.rules
        self.event_api = EventApi(self)
        app.flask_app.add_url_rule('/events', 'get_events', self.event_api.post, methods=['POST'])
        app.flask_app.add_url_rule('/events', 'post_events', self.event_api.get, methods=['GET'])


    def get(self, key, before_time, since_time, limit, offset):
        session = self.database.session()
        try:
            query = session.query(Event).order_by(Event.time.desc())
            if key is not None:
                validate.field_is_sha256(key, 'key')
                query = query.filter_by(key=key)
            if before_time is not None:
                query = query.filter(Event.time < before_time)
            if since_time is not None:
                query = query.filter(since_time < Event.time)
            if since_time is not None and before_time is not None and before_time < since_time:
                raise Exception('since_time is greater than before_time')
            if self.rules.events_limit_max < limit:
                raise Exception('limit greater than maximum allowed')
            if offset is not None:
                query = query.offset(offset)

            query = query.limit(limit)
            results = []
            for match in query.all():
                event_json = None
                for data in session.query(EventData).filter_by(event_id=match.id).all():
                    event_json = data.get_json()
                    if event_json is not None:
                        break
                if event_json is None:
                    print 'unable to find data for events.id %s' % match.id
                    continue
                results.append(event_json)
            return json.dumps(results)
        finally:
            session.close()


    def add(self, request_data):
        session = self.database.session()
        try:
            return True
        except:
            session.rollback()
            traceback.print_exc()
            return False
        finally:
            session.close()

