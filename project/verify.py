import util
from models import StarLog


def jump(session, fleet, inputs, outputs):
    if len(inputs) == 0:
        raise Exception('jump must contain at least one input')
    if len(outputs) == 0:
        raise Exception('jump must contain at least oun output')
    input_ship_count = 0
    origin_system_id = inputs[0].star_system_id
    for current_input in inputs:
        if current_input.fleet_id != fleet.id:
            raise Exception('jump must consist of ships from a single fleet')
        if current_input.star_system_id != origin_system_id:
            raise Exception('jump inputs must start from the same origin')
        input_ship_count += current_input.count
    output_ship_count = 0
    destination_system_id = None
    for current_output in outputs:
        if current_output.star_system_id != origin_system_id:
            destination_system_id = current_output.star_system_id
            break
    if destination_system_id is None:
        raise Exception('jump must consist of at least one '
                        'output in another system')
    for current_output in outputs:
        if current_output.fleet_id != fleet.id:
            raise Exception('jump must consist of ships from a single fleet')
        if current_output.star_system_id == origin_system_id:
            input_ship_count -= current_output.count
        elif current_output.star_system_id == destination_system_id:
            output_ship_count += current_output.count
        else:
            raise Exception('jump outputs must end in the '
                            'same origin or destination')
    origin_system = session.query(StarLog)\
        .filter_by(id=origin_system_id).first()
    destination_system = session.query(StarLog)\
        .filter_by(id=destination_system_id).first()
    ship_cost = util.get_jump_cost(origin_system.hash,
                                   destination_system.hash,
                                   input_ship_count)
    if ship_cost == input_ship_count:
        raise Exception('jump cannot have zero ships reach destination')
    if ship_cost != (input_ship_count - output_ship_count):
        raise Exception('jump cost does not match '
                        'expected cost of %s' % ship_cost)


def attack(fleet, inputs, outputs):
    if len(inputs) < 2:
        raise Exception('jump must contain at least two inputs')

    ship_count = 0
    enemy_ship_count = 0
    origin_system_id = inputs[0].star_system_id
    enemy_fleet_id = None
    for current_input in inputs:
        if current_input.star_system_id != origin_system_id:
            raise Exception('attack inputs must be from the same origin')
        if current_input.fleet_id == fleet.id:
            ship_count += current_input.count
        else:
            if enemy_fleet_id is None:
                enemy_fleet_id = current_input.fleet_id
            elif enemy_fleet_id != current_input.fleet_id:
                raise Exception('an attack may only consist of two fleets')
            enemy_ship_count += current_input.count

    output_ship_count = 0
    output_enemy_ship_count = 0
    for current_output in outputs:
        if current_output.count == 0:
            raise Exception('attack output cannot be zero')
        if current_output.star_system_id != origin_system_id:
            raise Exception('attack outputs must be in the same origin')
        if current_output.fleet_id == fleet.id:
            output_ship_count += current_output.count
        elif current_output.fleet_id == enemy_fleet_id:
            output_enemy_ship_count += current_output.count
        else:
            raise Exception('an attack output must be '
                            'from the original fleets')

    if ship_count < enemy_ship_count:
        if enemy_ship_count - ship_count != output_enemy_ship_count:
            raise Exception('attack input and output count mismatch')
    elif enemy_ship_count < ship_count:
        if ship_count - enemy_ship_count != output_ship_count:
            raise Exception('attack input and output count mismatch')
    elif output_ship_count + output_enemy_ship_count != 0:
        raise Exception('attack input and output count mismatch')
