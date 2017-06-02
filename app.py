import traceback
import logging
import os
import json
from flask import Flask, request

app = Flask(__name__)
app.debug = 0 < os.getenv('CV_DEBUG', 0)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_HOST', 'sqlite:///service.db')

# TODO: Do these still need to be separated from the rest of the imports?
import util
import validate
import verify
from models import database, StarLog, Fleet, Chain, ChainIndex, Event, EventSignature, EventInput, EventOutput, StarLogEventSignature

database.app = app
database.init_app(app)
database.create_all()


@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


@app.route('/')
def route_index():
    return 'Running'


@app.route("/rules")
def get_rules():
    return json.dumps({
        'difficulty_fudge': util.difficultyFudge(),
        'difficulty_duration': util.difficultyDuration(),
        'difficulty_interval': util.difficultyInterval(),
        'difficulty_start': util.difficultyStart(),
        'ship_reward': util.shipReward(),
        'cartesian_digits': util.cartesianDigits(),
        'jump_cost_min': util.jumpCostMinimum(),
        'jump_cost_max': util.jumpCostMaximum(),
        'jump_distance_max': util.jumpDistanceMaximum(),
        'star_logs_max_limit': util.starLogsMaxLimit(),
        'events_max_limit': util.eventsMaxLimit(),
        'chains_max_limit': util.chainsMaxLimit()
    })


@app.route('/chains')
def get_chains():
    session = database.session()
    try:
        height = request.args.get('height', None, type=int)
        limit = request.args.get('limit', 1, type=int)
        query = database.session.query(StarLog)
        if height is None:
            query = query.order_by(StarLog.height.desc())
        else:
            if height < 0:
                raise ValueError('height is out of range')
            query = query.filter_by(height=height)
        if util.chainsMaxLimit() < limit:
            raise ValueError('limit greater than maximum allowed')
        query = query.limit(limit)
        matches = query.all()
        results = []

        # TODO: Remove duplicate code that's in chains and starlogs.
        # TODO: Make this code better by figuring out joins and such.
        for match in matches:
            signature_binds = session.query(StarLogEventSignature).filter_by(star_log_id=match.id).all()
            events = []
            for signature_bind in signature_binds:
                signature_match = session.query(EventSignature).filter_by(id=signature_bind.event_signature_id).first()
                fleet = session.query(Fleet).filter_by(id=signature_match.fleet_id).first()
                input_events = session.query(EventInput).filter_by(event_signature_id=signature_match.id).all()
                output_events = session.query(EventOutput).filter_by(event_signature_id=signature_match.id).all()

                inputs = []
                for current_input in input_events:
                    current_input_event = session.query(Event).filter_by(id=current_input.event_id).first()
                    inputs.append(current_input.get_json(current_input_event.key))

                outputs = []
                for current_output in output_events:
                    current_output_event = session.query(Event).filter_by(id=current_output.event_id).first()
                    output_fleet = session.query(Fleet).filter_by(id=current_output_event.fleet_id).first()
                    output_star_system = session.query(StarLog).filter_by(id=current_output_event.star_system_id).first()
                    # Rewards sent to the probed system can't have been known, so they would be left blank.
                    output_star_system_hash = None if output_star_system.hash == match.hash else output_star_system.hash
                    outputs.append(current_output.get_json(util.get_event_type_name(current_output_event.type_id), output_fleet.hash, current_output_event.key, output_star_system_hash, current_output_event.count))
                events.append(signature_match.get_json(fleet.hash, fleet.public_key, inputs, outputs, signature_bind.index))
            results.append(match.get_json(events))

        return json.dumps(results)
    finally:
        session.close()


@app.route('/star-logs')
def get_star_logs():
    session = database.session()
    try:
        previous_hash = request.args.get('previous_hash', None, type=str)
        before_time = request.args.get('before_time', None, type=int)
        since_time = request.args.get('since_time', None, type=int)
        limit = request.args.get('limit', 1, type=int)
        offset = request.args.get('offset', None, type=int)
        query = session.query(StarLog).order_by(StarLog.time.desc())
        if previous_hash is not None:
            validate.field_is_sha256(previous_hash, 'previous_hash')
            query = query.filter_by(previous_hash=previous_hash)
        if before_time is not None:
            query = query.filter(StarLog.time < before_time)
        if since_time is not None:
            query = query.filter(since_time < StarLog.time)
        if since_time is not None and before_time is not None and before_time < since_time:
            raise ValueError('since_time is greater than before_time')
        if util.starLogsMaxLimit() < limit:
            raise ValueError('limit greater than maximum allowed')
        if offset is not None:
            query = query.offset(offset)

        query = query.limit(limit)
        matches = query.all()
        results = []
        # TODO: Remove duplicate code that's in chains and starlogs.
        # TODO: Make this code better by figuring out joins and such.
        for match in matches:
            signature_binds = session.query(StarLogEventSignature).filter_by(star_log_id=match.id).all()
            events = []
            for signature_bind in signature_binds:
                signature_match = session.query(EventSignature).filter_by(id=signature_bind.event_signature_id).first()
                fleet = session.query(Fleet).filter_by(id=signature_match.fleet_id).first()
                input_events = session.query(EventInput).filter_by(event_signature_id=signature_match.id).all()
                output_events = session.query(EventOutput).filter_by(event_signature_id=signature_match.id).all()

                inputs = []
                for current_input in input_events:
                    current_input_event = session.query(Event).filter_by(id=current_input.event_id).first()
                    inputs.append(current_input.get_json(current_input_event.key))

                outputs = []
                for current_output in output_events:
                    current_output_event = session.query(Event).filter_by(id=current_output.event_id).first()
                    output_fleet = session.query(Fleet).filter_by(id=current_output_event.fleet_id).first()
                    output_star_system = session.query(StarLog).filter_by(id=current_output_event.star_system_id).first()
                    # Rewards sent to the probed system can't have been known, so they would be left blank.
                    output_star_system_hash = None if output_star_system.hash == match.hash else output_star_system.hash
                    outputs.append(current_output.get_json(util.get_event_type_name(current_output_event.type_id), output_fleet.hash, current_output_event.key, output_star_system_hash, current_output_event.count))
                events.append(signature_match.get_json(fleet.hash, fleet.public_key, inputs, outputs, signature_bind.index))
            results.append(match.get_json(events))
        return json.dumps(results)
    finally:
        session.close()


@app.route('/star-logs', methods=['POST'])
def post_star_logs():
    session = database.session()
    try:
        validate.byte_size(util.maximumStarLogSize(), request.data)
        star_log_json = json.loads(request.data)
        validate.star_log(star_log_json)

        previous_chain = None
        previous_hash = star_log_json['previous_hash']
        is_genesis = util.is_genesis_star_log(previous_hash)
        if not is_genesis:
            previous_chain = session.query(ChainIndex).filter_by(hash=previous_hash).first()
            if previous_chain is None:
                raise ValueError('previous starlog with hash %s cannot be found' % previous_hash)

        chain_index = session.query(ChainIndex).filter_by(hash=star_log_json['hash']).first()
        if chain_index:
            raise ValueError('starlog with hash %s already exists' % chain_index.hash)

        highest_chain = session.query(Chain).order_by(Chain.chain.desc()).first()
        root_id = None
        previous_chain_id = None
        previous_star_log_id = None
        height = 0
        chain_count = 0

        if is_genesis:
            chain_count = 0 if highest_chain is None else highest_chain.chain + 1
        else:
            root_id = previous_chain.id if previous_chain.root_id is None else previous_chain.root_id
            previous_chain_id = previous_chain.id
            previous_star_log_id = previous_chain.star_log_id
            height = previous_chain.height + 1
            chain_count = previous_chain.chain

        chain = None

        if session.query(ChainIndex).filter_by(height=height, chain=chain_count).first():
            # A sibling chain is being created.
            root_id = None if is_genesis else previous_chain.id
            chain_count = highest_chain.chain + 1
            chain = Chain(height, None, chain_count, None)
            session.add(chain)
        elif is_genesis:
            chain = Chain(height, None, chain_count, None)
            session.add(chain)
        else:
            chain = session.query(Chain).filter_by(chain=chain_count).first()
            if chain is None:
                raise ValueError('no chain %s exists' % chain_count)
            chain.height = height

        chain_index = ChainIndex(root_id, previous_chain_id, None, previous_star_log_id, star_log_json['hash'], star_log_json['previous_hash'], height, chain_count)
        session.add(chain_index)
        session.flush()
        chain.head_index_id = chain_index.id

        needs_star_log_ids = [chain_index, chain]
        needs_star_system_ids = []

        previous_star_log = session.query(StarLog).filter_by(id=previous_star_log_id).first() if previous_star_log_id == 0 or previous_star_log_id is not None else None
        interval_id = None
        # If the previous StarLog has no interval_id, that means we recalculated difficulty on it.
        if previous_star_log is not None:
            interval_id = previous_star_log.interval_id if previous_star_log.interval_id == 0 or previous_star_log.interval_id is not None else previous_star_log.id

        if is_genesis:
            if star_log_json['difficulty'] != util.difficultyStart():
                raise ValueError('difficulty for genesis starlog does not match starting difficulty')
        elif util.is_difficulty_changing(height):
            interval_start = session.query(StarLog).filter_by(id=previous_star_log.interval_id).first()
            if interval_start is None:
                raise ValueError('unable to find interval start with id %s' % (previous_star_log.interval_id))
            duration = previous_star_log.time - interval_start.time
            difficulty = util.calculate_difficulty(previous_star_log.difficulty, duration)
            if star_log_json['difficulty'] != difficulty:
                raise ValueError('difficulty does not match recalculated difficulty')
            # This lets the next in the chain know to use our id for the interval_id.
            interval_id = None
        elif star_log_json['difficulty'] != previous_star_log.difficulty:
            raise ValueError('difficulty does not match previous difficulty')

        fleets_added = False
        for fleet in util.get_fleets(star_log_json['events']):
            fleet_hash, fleet_public_key = fleet
            if session.query(Fleet).filter_by(hash=fleet_hash).first() is None:
                session.add(Fleet(fleet_hash, fleet_public_key))
                fleets_added = True

        if fleets_added:
            session.flush()

        for current_event in star_log_json['events']:
            event_signature = session.query(EventSignature).filter_by(hash=current_event['hash']).first()
            fleet = session.query(Fleet).filter_by(hash=current_event['fleet_hash']).first()
            new_signature = event_signature is None
            if new_signature:
                event_signature = EventSignature(util.get_event_type_id(current_event['type']), fleet.id, current_event['hash'], current_event['signature'], util.get_time(), 1)
                session.add(event_signature)
                session.flush()
                event_signature_bind = StarLogEventSignature(event_signature.id, None, current_event['index'])
                session.add(event_signature_bind)
                needs_star_log_ids.append(event_signature_bind)
            else:
                additional_signature_bind = StarLogEventSignature(event_signature.id, None, current_event['index'])
                session.add(additional_signature_bind)
                needs_star_log_ids.append(additional_signature_bind)
                event_signature.confirmations += 1

            inputs = []
            for current_input in current_event['inputs']:
                # Check if we even have an input with the matching key.
                target_input = session.query(Event).filter_by(key=current_input['key']).first()
                if target_input is None:
                    raise Exception('event %s is not accounted for' % current_input['key'])
                # Append this for further validation.
                inputs.append(target_input)
                # Get all uses of this input.
                input_uses = session.query(EventInput).filter_by(event_id=target_input.id).all()
                # Build a list of all signatures that use this input.
                input_uses_signatures = []
                for input_use in input_uses:
                    if input_use.event_signature_id not in input_uses_signatures:
                        input_uses_signatures.append(input_use.event_signature_id)
                # Build a list of all starlogs that reference any of the matching signatures.
                signature_star_logs = []
                for input_uses_signature in input_uses_signatures:
                    for signatureBind in session.query(StarLogEventSignature).filter_by(event_signature_id=input_uses_signature).all():
                        if signatureBind.star_log_id not in signature_star_logs:
                            signature_star_logs.append(signatureBind.star_log_id)
                # TODO: Optimize this into one select call.
                # Make sure the signature is not used earlier in the chain.
                checked_chains = []
                for signature_star_log in signature_star_logs:
                    signature_chain_index = session.query(ChainIndex).filter_by(star_log_id=signature_star_log).first()
                    # If the height of this signature's usage is higher in the chain, then we're branching off, so we duck out here.
                    if height <= signature_chain_index.height:
                        continue
                    next_chain_index = signature_chain_index
                    while next_chain_index is not None:
                        if next_chain_index.chain in checked_chains:
                            break
                        else:
                            checked_chains.append(next_chain_index.chain)

                        if next_chain_index.chain == chain_index.chain:
                            raise Exception('event %s has already been used by %s' % (current_input['key'], next_chain_index.hash))
                        next_chain_index = None if next_chain_index.root_id is None else session.query(ChainIndex).filter_by(id=next_chain_index.root_id).first()
                # Now we need to make sure each individual input actually exists, and wasn't created in a higher chain.
                input_origin = session.query(EventOutput).filter_by(event_id=target_input.id).first()
                if input_origin is None:
                    raise Exception('output event of input %s not accounted for' % current_input['key'])
                origin_binds = session.query(StarLogEventSignature).filter_by(event_signature_id=input_origin.event_signature_id).all()
                validated_origin = False
                origin_checked_chains = []
                for origin_bind in origin_binds:
                    origin_chain_index = session.query(ChainIndex).filter_by(star_log_id=origin_bind.star_log_id).first()
                    # We don't care about higher origins
                    if height <= origin_chain_index.height:
                        continue
                    next_chain_index = chain_index
                    while next_chain_index is not None:
                        if next_chain_index.chain in origin_checked_chains:
                            break
                        else:
                            origin_checked_chains.append(next_chain_index.chain)
                        if next_chain_index.chain == origin_chain_index.chain:
                            validated_origin = True
                            break
                        next_chain_index = None if next_chain_index.root_id is None else session.query(ChainIndex).filter_by(id=next_chain_index.root_id).first()
                if not validated_origin:
                    raise Exception('event input %s does not have a valid output event' % current_input['key'])
                if new_signature:
                    session.add(EventInput(target_input.id, event_signature.id, current_input['index']))

            outputs = []
            for current_output in current_event['outputs']:
                target_output = None
                event_output = None
                if new_signature:
                    if session.query(Event).filter_by(key=current_output['key']).first():
                        raise Exception('output key %s already exists' % current_output['key'])
                    output_fleet = session.query(Fleet).filter_by(hash=current_output['fleet_hash']).first()
                    if output_fleet is None:
                        output_fleet = Fleet(current_output['fleet_hash'], None)
                        session.add(output_fleet)
                        session.flush()
                    target_star_system_id = None
                    if current_output['star_system']:
                        target_star_system = session.query(StarLog).filter_by(hash=current_output['star_system']).first()
                        if target_star_system is None:
                            raise Exception('star system %s is not accounted for' % current_output['star_system'])
                        target_star_system_id = target_star_system.id
                    target_output = Event(current_output['key'], util.get_event_type_id(current_output['type']), output_fleet.id, current_output['count'], target_star_system_id)
                    session.add(target_output)
                    session.flush()
                    if target_star_system_id is None:
                        needs_star_system_ids.append(target_output)
                    event_output = EventOutput(target_output.id, event_signature.id, current_output['index'])
                    session.add(event_output)
                else:
                    target_output = session.query(Event).filter_by(key=current_output['key']).first()
                    event_output = session.query(EventOutput).filter_by(index=current_output['index'], event_id=target_output.id, event_signature_id=event_signature.id)
                # Append this for further validation.
                outputs.append(target_output)

            if current_event['type'] == 'jump':
                verify.jump(session, fleet, inputs, outputs)
            elif current_event['type'] == 'attack':
                verify.attack(fleet, inputs, outputs)
            elif current_event['type'] == 'transfer':
                verify.transfer(fleet, inputs, outputs)
            elif current_event['type'] not in ['reward']:
                raise Exception('event type %s not supported' % current_event['type'])

        star_log = StarLog(
            star_log_json['hash'], 
            chain_index.id, height, 
            len(request.data), 
            star_log_json['log_header'], 
            star_log_json['version'], 
            star_log_json['previous_hash'], 
            star_log_json['difficulty'], 
            star_log_json['nonce'], 
            star_log_json['time'], 
            star_log_json['events_hash'], 
            interval_id, 
            star_log_json['meta'],
            star_log_json['meta_hash']
        )
        session.add(star_log)
        session.flush()
        for entry in needs_star_log_ids:
            entry.star_log_id = star_log.id
        for entry in needs_star_system_ids:
            entry.star_system_id = star_log.id
        session.commit()
        return '200', 200
    except:
        session.rollback()
        traceback.print_exc()
        return '400', 400
    finally:
        session.close()


@app.route('/events')
def get_events():
    session = database.session()
    try:
        limit = request.args.get('limit', 1, type=int)

        if util.eventsMaxLimit() < limit:
            raise ValueError('limit greater than maximum allowed')

        # Don't get reward event signatures, since they'll always be associated with an existing block.
        # TODO: Order by confirmation counts, less confirmations should appear first.
        signatures = session.query(EventSignature).order_by(EventSignature.time.desc()).filter(EventSignature.type_id != util.get_event_type_id('reward')).limit(limit)
        results = []

        for signature in signatures:
            fleet = session.query(Fleet).filter_by(id=signature.fleet_id).first()

            inputs = []
            for current_input in session.query(EventInput).filter_by(event_signature_id=signature.id).all():
                current_input_event = session.query(Event).filter_by(id=current_input.event_id).first()
                inputs.append(current_input.get_json(current_input_event.key))

            outputs = []
            for current_output in session.query(EventOutput).filter_by(event_signature_id=signature.id).all():
                current_output_event = session.query(Event).filter_by(id=current_output.event_id).first()
                output_fleet = session.query(Fleet).filter_by(id=current_output_event.fleet_id).first()
                output_star_system = session.query(StarLog).filter_by(id=current_output_event.star_system_id).first()
                outputs.append(current_output.get_json(util.get_event_type_name(current_output_event.type_id), output_fleet.hash, current_output_event.key, output_star_system.hash, current_output_event.count))

            results.append(signature.get_json(fleet.hash, fleet.public_key, inputs, outputs, None))
        return json.dumps(results)
    finally:
        session.close()


@app.route('/events', methods=['POST'])
def post_events():
    session = database.session()
    try:
        validate.byte_size(util.maximumEventSize(), request.data)
        event_json = json.loads(request.data)
        validate.event(event_json, False, True, False)

        if session.query(EventSignature).filter_by(hash=event_json['hash']).first():
            raise Exception('event with hash %s already exists' % event_json['hash'])

        fleet = session.query(Fleet).filter_by(hash=event_json['fleet_hash']).first()

        event_signature = EventSignature(util.get_event_type_id(event_json['type']), fleet.id, event_json['hash'], event_json['signature'], util.get_time(), 0)
        session.add(event_signature)
        session.flush()
        inputs = []
        for current_input in event_json['inputs']:
            target_input = session.query(Event).filter_by(key=current_input['key']).first()
            if target_input is None:
                raise Exception('event with key %s not accounted for' % current_input['key'])
            inputs.append(target_input)
            session.add(EventInput(target_input.id, event_signature.id, current_input['index']))
        outputs = []
        for current_output in event_json['outputs']:
            target_output = session.query(Event).filter_by(key=current_output['key']).first()
            if target_output is None:
                output_fleet = session.query(Fleet).filter_by(hash=current_output['fleet_hash']).first()
                if output_fleet is None:
                    output_fleet = Fleet(current_output['fleet_hash'], None)
                    session.add(output_fleet)
                    session.flush()
                target_star_system = session.query(StarLog).filter_by(hash=current_output['star_system']).first()
                if target_star_system is None:
                    raise Exception('star system %s is not accounted for' % current_output['star_system'])

                target_output = Event(current_output['key'], util.get_event_type_id(current_output['type']), output_fleet.id, current_output['count'], target_star_system.id)
                session.add(target_output)
                session.flush()
            outputs.append(target_output)
            event_output = EventOutput(target_output.id, event_signature.id, current_output['index'])
            session.add(event_output)
        if event_json['type'] == 'jump':
            verify.jump(session, fleet, inputs, outputs)
        elif event_json['type'] == 'attack':
            verify.attack(fleet, inputs, outputs)
        elif event_json['type'] == 'transfer':
            verify.transfer(fleet, inputs, outputs)
        else:
            raise Exception('event type %s not supported' % event_json['type'])

        session.commit()
        return '200', 200
    except:
        session.rollback()
        traceback.print_exc()
        return '400', 400
    finally:
        session.close()

if __name__ == '__main__':
    if 0 < util.difficultyFudge():
        app.logger.info('All hash difficulties will be calculated with DIFFICULTY_FUDGE %s' % (util.difficultyFudge()))
    app.run(use_reloader=False)
