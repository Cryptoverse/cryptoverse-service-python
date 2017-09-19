import json
import traceback
from cvservice import util
from cvservice import validate
from cvservice.models.block import Block
from cvservice.models.block_data import BlockData
from cvservice.views.block_api import BlockApi

class BlockController(object):

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
            self.validate_block(block_json)
            # block_json = json.loads(request_data)
            # block = Block(block_json['hash'],
            #               block_json['previous_hash'],
            #               None, # previous_id
            #               block_json['height'],
            #               None, # size
            #               block_json['version'],
            #               block_json['difficulty'],
            #               block_json['time'],
            #               None, # interval_id
            #               None, # root_id
            #               None) # chain
            # session.add(block)
            # session.commit()
            return True
        except:
            session.rollback()
            traceback.print_exc()
            return False
        finally:
            session.close()

    def validate_block(self, block_json):
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
            self.validate_event(current_event)
            events_header += current_event['hash']
        validate.sha256(block_json['events_hash'], events_header)

    def validate_event(self, event_json):
        if event_json['inputs'] is None:
            raise Exception('inputs cannot be None')
        if event_json['hash'] is None:
            raise Exception('hash cannot be None')
        if event_json['fleet_hash'] is None:
            raise Exception('fleet_hash cannot be None')
        if event_json['fleet_key'] is None:
            raise Exception('fleet_key cannot be None')
        if event_json['outputs'] is None:
            raise Exception('outputs cannot be None')
        if event_json['type'] is None:
            raise Exception('type cannot be None')
        
        # TODO: Check that the event type is supported.

        validate.field_is_sha256(event_json['hash'], 'hash')
        validate.field_is_sha256(event_json['fleet_hash'], 'fleet_hash')

        validate.sha256(event_json['fleet_hash'], event_json['fleet_key'])

        event_header = '%s%s%s' % (event_json['fleet_hash'], event_json['fleet_key'], event_json['type'])
        for current_input in sorted(event_json['inputs'], key=lambda x: x['index']):
            self.validate_event_input(current_input)
            event_header += current_input['key']
        for current_output in sorted(event_json['outputs'], key=lambda x: x['index']):
            self.validate_event_output(current_output)

            serialized_location = '' if current_output['location'] is None else current_output['location']
            event_header += '%s%s%s%s' % (current_output['type'], current_output['fleet_hash'], current_output['key'], serialized_location)
            event_header += self.concat_event_output_model(current_output['model'])
        validate.sha256(event_json['hash'], event_header)

    def validate_event_input(self, event_input_json):
        if event_input_json['key'] is None:
            raise Exception('key cannot be None')

    def validate_event_output(self, event_output_json):
        if event_output_json['fleet_hash'] is None:
            raise Exception('fleet_hash cannot be None')
        if event_output_json['key'] is None:
            raise Exception('key cannot be None')
        if event_output_json['type'] is None:
            raise Exception('type cannot be None')
        if event_output_json['model'] is None:
            raise Exception('model cannot be None')

    def concat_event_output_model(self, event_output_model_json):
        model_type = event_output_model_json['type']
        if model_type == 'vessel':
            return self.concat_vessel(event_output_model_json)
        raise Exception('event output model "%s" is not recognized' % model_type)

    def concat_vessel(self, vessel_json):
        if vessel_json['blueprint'] is None:
            raise Exception('blueprint cannot be None')
        if vessel_json['modules'] is None:
            raise Exception('modules cannot be None')
        vessel_header = vessel_json['blueprint']
        for current_module in sorted(vessel_json['modules'], key=lambda x: x['index']):
            vessel_header += self.concat_module(current_module)
        return vessel_header

    def concat_module(self, module_json):
        if module_json['blueprint'] is None:
            raise Exception('blueprint cannot be None')
        if module_json['delta'] is None:
            raise Exception('delta cannot be None')
        if module_json['health'] is None:
            raise Exception('health cannot be None')
        module_type = module_json['type']
        module_header = '%s%s%s' % (module_json['blueprint'], module_json['delta'], module_json['health'])
        
        if module_type == 'cargo':
            module_header += self.concat_cargo(module_json)
        elif module_type == 'jump_drive':
            module_header += self.concat_jump_drive(module_json)
        else:
            raise Exception('%s not a recognized module type' % module_type)
        return module_header

    def concat_cargo(self, cargo_json):
        if cargo_json['contents'] is None:
            raise Exception('contents cannot be None')
        cargo_header = self.concat_resources(cargo_json['contents'])
        return cargo_header
    
    def concat_jump_drive(self, jump_drive_json):
        return ''

    def concat_resources(self, resources_json):
        resources_header = str(resources_json.get('fuel', ''))
        return resources_header

        # query = session.query(Block).order_by(Block.time.desc())
        # if block_json['previous_hash'] is None:
        #     raise Exception('previous_hash in None')
        # validate.field_is_sha256(block_json['previous_hash'], 'previous_hash')
        # query = query.filter_by(hash=['previous_hash'])
        
        # result = query.all()
        # if result is None:
        #     raise Exception('Unable to find previous_hash %s' % block_json['previous_hash'])

        # result_json = 
        # for match in :
        #     blob = None
        #     for data in session.query(BlockData).filter_by(block_id=match.id).all():
        #         if data.data is not None:
        #             blob = data.blob
        #             break
        #     if blob is None:
        #         print 'unable to find blob for block.id %s' % match.id
        #         continue
        #     print blob
        # return json.dumps(results)
