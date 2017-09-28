from flask import request

class EventApi(object):

    def __init__(self, event_controller):
        self.event_controller = event_controller


    def get(self):
        # key, before_time, since_time, limit, offset
        key = request.args.get('key', None, type=str)
        before_time = request.args.get('before_time', None, type=int)
        since_time = request.args.get('since_time', None, type=int)
        limit = request.args.get('limit', 1, type=int)
        offset = request.args.get('offset', None, type=int)
        
        return self.event_controller.get(key,
                                         before_time,
                                         since_time,
                                         limit,
                                         offset)


    def post(self):
        result = self.event_controller.add(request.data)
        if result:
            return "200", 200
        else:
            return "400", 400