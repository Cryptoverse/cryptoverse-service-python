import util
from models import (
    StarLog, Fleet, Chain, ChainIndex, ChainIndex, Event,
    EventSignature, EventInput, EventOutput, StarLogEventSignature,
    EventModelType, HullBlueprint, JumpDriveBlueprint, CargoBlueprint,
    JumpDrive, Cargo, EventModel
)

def star_log(session, star_log_record):
    signature_binds = session.query(StarLogEventSignature).filter_by(star_log_id=star_log_record.id).all()
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
            output_star_system_hash = None if output_star_system.hash == star_log_record.hash else output_star_system.hash
            model_type = util.get_event_model_type_name(current_output_event.model_type_id)
            model = None
            if model_type == 'vessel':
                model = {
                    'blueprint': None,
                    'modules': []
                }
                for current_event_module in session.query(EventModel).filter_by(event_id=current_output.event_id):
                    current_module_type = util.get_module_type_name(current_event_module.type_id)
                    if current_module_type == 'hull':
                        model['blueprint'] = session.query(HullBlueprint).filter_by(id=current_event_module.model_id).first().hash
                    elif current_module_type == 'jump_drive':
                        current_module = session.query(JumpDrive).filter_by(id=current_event_module.model_id).first()
                        current_blueprint = session.query(JumpDriveBlueprint).filter_by(id=current_module.blueprint_id).first()
                        model['modules'].append(current_module.get_json(current_blueprint.hash))
                    elif current_module_type == 'cargo':
                        current_module = session.query(Cargo).filter_by(id=current_event_module.model_id).first()
                        current_blueprint = session.query(CargoBlueprint).filter_by(id=current_module.blueprint_id).first()
                        model['modules'].append(current_module.get_json(current_blueprint.hash))
                    else:
                        raise Exception('module type %s not implimented' % current_module_type)
            else:
                raise Exception('event type %s not implimented' % model_type)
            outputs.append(current_output.get_json(util.get_event_type_name(current_output_event.type_id), output_fleet.hash, current_output_event.key, output_star_system_hash, model, model_type))

        events.append(signature_match.get_json(fleet.hash, fleet.public_key, inputs, outputs, signature_bind.index))
    return star_log_record.get_json(events)