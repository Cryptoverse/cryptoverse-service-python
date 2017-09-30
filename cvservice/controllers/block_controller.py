import json
import traceback
from collections import namedtuple
from cvservice import util
from cvservice import validate
from cvservice.models.block import Block
from cvservice.models.block_data import BlockData
from cvservice.views.block_api import BlockApi

class BlockController(object):

    def __init__(self, app):
        self.app = app
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
            
            if limit is None:
                limit = self.rules.blocks_limit_max
            else:
                if limit < 1:
                    raise Exception('limit must be greater than zero')
                if self.rules.blocks_limit_max < limit:
                    raise Exception('limit greater than maximum allowed')
            
            query = query.limit(limit)
            
            if offset is not None:
                query = query.offset(offset)

            results = []
            for match in query.all():
                block_json = None
                for data in session.query(BlockData).filter_by(block_id=match.block_id).all():
                    block_json = data.get_json()
                    if block_json is not None:
                        break
                if block_json is None:
                    print 'unable to find data for blocks.id %s' % match.block_id
                    continue
                results.append(block_json)
            return json.dumps(results)
        finally:
            session.close()


    def add(self, request_data):
        session = self.database.session()
        try:
            validate.byte_size(self.rules.block_size, request_data)
            block_size = len(request_data)
            block_json = json.loads(request_data)
            self.validate_block(session, block_json)
            
            block = Block(block_json['hash'],
                          block_json['previous_hash'],
                          None, # previous_id
                          block_json['height'],
                          block_size,
                          block_json['version'],
                          block_json['difficulty'],
                          block_json['time'],
                          None, # interval_id
                          None, # root_id
                          None) # chain

            if self.rules.is_genesis_block(block_json['previous_hash']):
                block.chain = util.get_unique_key()
            else:
                previous_block = session.query(Block).filter_by(block_hash=block_json['previous_hash']).first()
                if previous_block is None:
                    raise Exception('unable to find previous block with hash %s' % block_json['previous_hash'])
                if block_json['height'] != previous_block.height + 1:
                    raise Exception('wrong height specified')
                block.previous_id = previous_block.block_id

                if self.rules.is_difficulty_changing(block_json['height']):
                    interval_start = session.query(Block).filter_by(id=previous_block.interval_id).first()
                    if interval_start is None:
                        raise Exception('unable to find interval start with id %s' % (previous_block.interval_id))
                    duration = previous_block.time - interval_start.time
                    difficulty = self.rules.calculate_difficulty(previous_block.difficulty, duration)
                    if block_json['difficulty'] != difficulty:
                        raise Exception('difficulty does not match recalculated difficulty')
                    # This lets the next in the chain know to use our id for the interval_id.
                    block.interval_id = None
                elif block_json['difficulty'] != previous_block.difficulty:
                    raise Exception('difficulty does not match previous difficulty')
                else:
                    block.interval_id = previous_block.block_id if previous_block.interval_id is None else previous_block.interval_id

                if session.query(Block).filter_by(height=block_json['height'], chain=previous_block.chain).first():
                    # A sibling chain is being created.
                    block.root_id = previous_block.block_id
                    block.chain = util.get_unique_key()
                else:
                    block.root_id = previous_block.block_id if previous_block.root_id is None else previous_block.root_id
                    block.chain = previous_block.chain
                self.app.event_controller.verify_events(session, block_json, previous_block.block_id)

            self.app.event_controller.add_all(session, block_json['events'], True)
            
            session.add(block)
            session.flush()

            block_data = BlockData(block.block_id,
                                   block.previous_id,
                                   'data_json', # Not really used at the moment, will eventually lead to a path on disk
                                   request_data)
            session.add(block_data)

            session.commit()
            return True
        except:
            session.rollback()
            traceback.print_exc()
            return False
        finally:
            session.close()


    def validate_block(self, session, block_json):
        if block_json['hash'] is None:
            raise Exception('hash cannot be None')
        if block_json['nonce'] is None:
            raise Exception('nonce cannot be None')
        if block_json['height'] is None:
            raise Exception('height cannot be None')
        if block_json['difficulty'] is None:
            raise Exception('difficulty cannot be None')
        if block_json['events_hash'] is None:
            raise Exception('events_hash cannot be None')
        if block_json['version'] is None:
            raise Exception('version cannot be None')
        if block_json['time'] is None:
            raise Exception('nonce cannot be None')
        if block_json['previous_hash'] is None:
            raise Exception('previous_hash cannot be None')
        if block_json['events'] is None:
            raise Exception('events cannot be None')
        
        validate.field_is_sha256(block_json['hash'], 'hash')
        validate.field_is_sha256(block_json['events_hash'], 'events_hash')

        log_header = str(block_json['version'])
        log_header += block_json['previous_hash']
        log_header += str(block_json['difficulty'])
        log_header += block_json['events_hash']
        log_header += util.sha256(block_json['meta'])
        log_header += str(block_json['time'])
        log_header += str(block_json['nonce'])
        
        validate.sha256(block_json['hash'], log_header)

        events_header = ''
        for current_event in sorted(block_json['events'], key=lambda x: x['index']):
            self.app.event_controller.validate_event(current_event)
            events_header += current_event['hash']
        validate.sha256(block_json['events_hash'], events_header)

        self.validate_is_new(session, block_json)

        if self.rules.is_genesis_block(block_json['previous_hash']):
            self.validate_genesis(session, block_json)
            return

        # TODO: Validate events and such, anything that's not in a genesis block...


    def validate_genesis(self, session, block_json):
        pass


    def validate_is_new(self, session, block_json):
        query = session.query(Block).filter_by(block_hash=block_json['hash'])
        result = query.first()
        if result is not None:
            raise Exception('block with hash %s already exists')
