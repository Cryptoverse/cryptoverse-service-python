import json
import traceback
from cvservice import validate
from cvservice.models.block import Block
from cvservice.models.block_data import BlockData
from cvservice.views.block_api import BlockApi

class BlockController():

    def __init__(self, app):
        self.database = app.database
        self.rules = app.rules
        self.block_api = BlockApi(self)
        app.flask_app.add_url_rule('/blocks', 'get_blocks', self.block_api.post, methods=['POST'])
        app.flask_app.add_url_rule('/blocks', 'post_blocks', self.block_api.get, methods=['GET'])

    def get(self, previous_hash, before_time, since_time, limit, offset):
        session = self.database.session()
        try:
            query = session.query(Block).order_by(Block.time.desc())
            if previous_hash is not None:
                validate.field_is_sha256(previous_hash, 'previous_hash')
                query = query.filter_by(previous_hash=previous_hash)
            if before_time is not None:
                query = query.filter(Block.time < before_time)
            if since_time is not None:
                query = query.filter(since_time < Block.time)
            if since_time is not None and before_time is not None and before_time < since_time:
                raise Exception('since_time is greater than before_time')
            if self.rules.blocks_limit_max < limit:
                raise Exception('limit greater than maximum allowed')
            if offset is not None:
                query = query.offset(offset)

            query = query.limit(limit)
            results = []
            for match in query.all():
                blob = None
                for data in session.query(BlockData).filter_by(block_id=match.id).all():
                    if data.data is not None:
                        blob = data.blob
                        break
                if blob is None:
                    print 'unable to find blob for block.id %s' % match.id
                    continue
                print blob
            return json.dumps(results)
        finally:
            session.close()
    
    def add(self, request_data):
        session = self.database.session()
        try:
            block_json = json.loads(request_data)
            block = Block(block_json['hash'],
                          block_json['previous_hash'],
                          None, # previous_id
                          None, # height
                          None, # size
                          block_json['version'],
                          block_json['difficulty'],
                          block_json['time'],
                          None, # interval_id
                          None, # root_id
                          None) # chain
            session.add(block)
            session.commit()
            return True
        except:
            session.rollback()
            traceback.print_exc()
            return False
        finally:
            session.close()