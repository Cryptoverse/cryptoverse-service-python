from flask import request

class BlockApi():

    def __init__(self, block_controller):
        self.block_controller = block_controller

    def get(self):
        previous_hash = request.args.get('previous_hash', None, type=str)
        before_time = request.args.get('before_time', None, type=int)
        since_time = request.args.get('since_time', None, type=int)
        limit = request.args.get('limit', None, type=int)
        offset = request.args.get('offset', None, type=int)
        
        return self.block_controller.get(previous_hash,
                                         before_time,
                                         since_time,
                                         limit,
                                         offset)


    def post(self):
        result = self.block_controller.add(request.data)
        if result:
            return "200", 200
        else:
            return "400", 400