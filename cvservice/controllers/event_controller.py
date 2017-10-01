import json
import traceback
from collections import namedtuple
from cvservice import util
from cvservice import validate
from cvservice.views.event_api import EventApi
from cvservice.models.event import Event
from cvservice.models.event_data import EventData
from cvservice.models.block_data import BlockData

class EventController(object):

    def __init__(self, app):
        self.database = app.database
        self.rules = app.rules
        self.event_api = EventApi(self)
        app.flask_app.add_url_rule('/events', 'get_events', self.event_api.post, methods=['POST'])
        app.flask_app.add_url_rule('/events', 'post_events', self.event_api.get, methods=['GET'])


    def get(self,
            event_hash,
            before_time,
            since_time,
            limit,
            offset,
            include_rewards):
        session = self.database.session()
        try:
            query = session.query(Event).order_by(Event.received_time.desc())
            if event_hash is not None:
                validate.field_is_sha256(event_hash, 'hash')
                query = query.filter_by(event_hash=event_hash)
            if before_time is not None:
                query = query.filter(Event.received_time < before_time)
            if since_time is not None:
                query = query.filter(since_time < Event.received_time)
            if since_time is not None and before_time is not None and before_time < since_time:
                raise Exception('since_time is greater than before_time')
            if include_rewards is None:
                include_rewards = False
            if not include_rewards:
                query = query.filter(Event.event_type != 'reward')

            if limit is None:
                limit = self.rules.events_limit_max
            else:
                if limit < 1:
                    raise Exception('limit must be greater than zero')
                if self.rules.events_limit_max < limit:
                    raise Exception('limit greater than maximum allowed')
            query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            results = []
            for match in query.all():
                event_json = None
                for data in session.query(EventData).filter_by(event_id=match.event_id).all():
                    event_json = data.get_json()
                    if event_json is not None:
                        break
                if event_json is None:
                    print 'unable to find data for events.id %s' % match.event_id
                    continue
                event_json['confirmation_count'] = match.confirmation_count
                results.append(event_json)
            return json.dumps(results)
        finally:
            session.close()


    def add(self, request_data):
        session = self.database.session()
        try:
            self.add_all(session, json.loads(request_data), allow_rewards=False)
            return True
        except:
            session.rollback()
            traceback.print_exc()
            return False
        finally:
            session.close()


    def add_all(self, session, events_json, confirm=False, allow_rewards=True):
        for event_json in events_json:
            self.validate_event(event_json)
            if not allow_rewards and event_json['type'] == 'reward':
                raise Exception('events of type reward are not allowed')
            existing_event = session.query(Event).filter_by(event_hash=event_json['hash']).first()

            if existing_event is None:
                event = Event(event_json['hash'],
                            event_json['key'],
                            event_json['type'],
                            None, # Size
                            event_json['version'],
                            util.get_time(),
                            1 if confirm else 0)
                
                session.add(event)
                session.flush()

                event_data = EventData(event.event_id,
                                    'data_json', # Not really used at the moment, will eventually lead to a path on disk
                                    json.dumps(event_json))
                session.add(event_data)
            elif confirm:
                existing_event.confirmation_count += 1

        session.commit()


    def verify_events(self, session, block_json, previous_id):
        EventMatches = namedtuple('EventMatches', ['event', 'remaining_inputs', 'inputs'])
        input_hashes = []
        event_matches = []
        events_found = 0
        for event in block_json['events']:
            self.validate_event(event)
            match_entry = EventMatches(event=event, remaining_inputs=[], inputs=[])
            match_entry.remaining_inputs.extend([x['hash'] for x in event['inputs']])
            input_hashes.extend(x for x in match_entry.remaining_inputs if x not in input_hashes)
            event_matches.append(match_entry)
        all_input_hashes = list(input_hashes)
        event_total = len(block_json['events'])
        
        while previous_id is not None and events_found != event_total:
            previous_data = session.query(BlockData).filter_by(block_id=previous_id, uri='data_json').first()
            if previous_data is None:
                raise Exception('unable to find block_data with id %s and uri %s' % (previous_id, 'data_json'))
            previous_json = previous_data.get_json()
            for previous_event in previous_json['events']:
                for current_input_hash in [x['hash'] for x in previous_event['inputs']]:
                    if current_input_hash in all_input_hashes:
                        raise Exception('event %s has already been used as a previous input')
                for current_output in previous_event['outputs']:
                    if current_output['hash'] in input_hashes:
                        receiving_events = [x for x in event_matches if current_output['hash'] in x.remaining_inputs]
                        for current_event in receiving_events:
                            current_event.remaining_inputs.remove(current_output['hash'])
                            current_event.inputs.append(current_output)
                            if len(current_event.remaining_inputs) == 0:
                                events_found += 1
            previous_id = previous_data.previous_block_id
        # TODO: Still need to loop through and confirm event rules are followed


    def validate_event(self, event_json):
        if event_json['inputs'] is None:
            raise Exception('inputs cannot be None')
        if event_json['hash'] is None:
            raise Exception('hash cannot be None')
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

        event_header = '%s%s%s%s%s' % (event_json['version'], 
                                       event_json['key'], 
                                       event_json['fleet_hash'], 
                                       event_json['fleet_key'], 
                                       event_json['type'])

        for current_input in sorted(event_json['inputs'], key=lambda x: x['index']):
            self.validate_event_input(current_input)
            event_header += current_input['hash']
        for current_output in sorted(event_json['outputs'], key=lambda x: x['index']):
            self.validate_event_output(current_output)
            serialized_location = '' if current_output['location'] is None else current_output['location']
            output_header = '%s%s%s%s' % (current_output['type'], current_output['fleet_hash'], current_output['key'], serialized_location)
            output_header += self.concat_event_output_model(current_output['model'])
            validate.sha256(current_output['hash'], output_header)
            event_header += current_output['hash']

        validate.sha256(event_json['hash'], event_header)

        if event_json['type'] == 'reward':
            self.validate_reward_event(event_json)
        else:
            # check if this is an attack, etc
            raise NotImplementedError


    def validate_reward_event(self, reward_json):
        if 0 < len(reward_json['inputs']):
            raise Exception('reward event should have no inputs')
        if 1 < len(reward_json['outputs']):
            raise Exception('reward event should have one output')
        output_json = reward_json['outputs'][0]
        if output_json['type'] != 'reward':
            raise Exception('reward output needs to be of type reward')
        model_json = output_json['model']
        if model_json is None:
            raise Exception('reward requires a model')
        if model_json['type'] != 'vessel':
            raise Exception('reward must be a vessel')
        if model_json['blueprint'] != self.rules.default_hull['blueprint']:
            raise Exception('reward hull does not match default')
        modules_json = model_json['modules']
        if len(modules_json) != 2:
            raise Exception('reward vessel has incorrect number of modules')
        cargo_json = [x for x in modules_json if x['index'] == 0]
        if len(cargo_json) == 0:
            raise Exception('unable to find reward cargo module')
        cargo_json = cargo_json[0]
        if cargo_json['type'] != 'cargo':
            raise Exception('first module must be cargo module')
        if cargo_json['blueprint'] != self.rules.default_cargo['blueprint']:
            raise Exception('reward cargo blueprint does not match default')
        if cargo_json['health'] != self.rules.default_cargo['health']:
            raise Exception('cargo health does not match default')
        contents_json = cargo_json['contents']
        if contents_json is None:
            raise Exception('reward cargo required to be full of fuel')

        # TODO: get mass limit from blueprint and verify fuel amount here.

        jump_drive_json = [x for x in modules_json if x['index'] == 1]
        if len(jump_drive_json) == 0:
            raise Exception('unable to find jump drive module')
        jump_drive_json = jump_drive_json[0]
        if jump_drive_json['type'] != 'jump_drive':
            raise Exception('second module must be jump drive module')
        if jump_drive_json['blueprint'] != self.rules.default_jump_drive['blueprint']:
            raise Exception('reward jump_drive blueprint does not match default')
        if jump_drive_json['health'] != self.rules.default_jump_drive['health']:
            raise Exception('jump_drive health does not match default')

        # TODO: Validate signatures?


    def validate_event_input(self, event_input_json):
        if event_input_json['hash'] is None:
            raise Exception('hash cannot be None')


    def validate_event_output(self, event_output_json):
        if event_output_json['fleet_hash'] is None:
            raise Exception('fleet_hash cannot be None')
        if event_output_json['hash'] is None:
            raise Exception('hash cannot be None')
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