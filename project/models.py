from flask_sqlalchemy import SQLAlchemy, SignallingSession, SessionBase
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean
from blueprints import DEFAULT_HULL, DEFAULT_CARGO, DEFAULT_JUMP_DRIVE
import util

class _SignallingSession(SignallingSession):
    """A subclass of `SignallingSession` that allows for `binds` to be specified
    in the `options` keyword arguments.

    """
    def __init__(self, db, autocommit=False, autoflush=True, **options):
        self.app = db.get_app()
        self._model_changes = {}
        self.emit_modification_signals = self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS']

        bind = options.pop('bind', None)
        if bind is None:
            bind = db.engine

        binds = options.pop('binds', None)
        if binds is None:
            binds = db.get_binds(self.app)

        SessionBase.__init__(self,
                             autocommit=autocommit,
                             autoflush=autoflush,
                             bind=bind,
                             binds=binds,
                             **options)


class _SQLAlchemy(SQLAlchemy):
    """A subclass of `SQLAlchemy` that uses `_SignallingSession`."""
    def create_session(self, options):
        return _SignallingSession(self, **options)


database = _SQLAlchemy()

# database = SQLAlchemy()


class StarLog(database.Model):
    __tablename__ = 'star_logs'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    hash = Column(String(64))
    chain_index_id = Column(Integer, ForeignKey('chain_indices.id'))
    height = Column(Integer)
    size = Column(Integer)
    log_header = Column(String(255))
    version = Column(Integer)
    previous_hash = Column(String(64))
    difficulty = Column(Integer)
    nonce = Column(Integer)
    time = Column(Integer)
    events_hash = Column(String(64))
    interval_id = Column(Integer, ForeignKey('star_logs.id'))
    meta = Column(String(255))
    meta_hash = Column(String(64))

    def __repr__(self):
        return '<StarLog %r>' % self.hash

    def __init__(self,
                 hash,
                 chain_index_id,
                 height,
                 size,
                 log_header,
                 version,
                 previous_hash,
                 difficulty,
                 nonce,
                 time,
                 events_hash,
                 interval_id,
                 meta,
                 meta_hash):
        self.hash = hash
        self.chain_index_id = chain_index_id
        self.height = height
        self.size = size
        self.log_header = log_header
        self.version = version
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = nonce
        self.time = time
        self.events_hash = events_hash
        self.interval_id = interval_id
        self.meta = meta
        self.meta_hash = meta_hash

    def get_json(self, events):
        return {
            'create_time': self.time,
            'hash': self.hash,
            'height': self.height,
            'meta': self.meta,
            'meta_hash': self.meta_hash,
            'log_header': self.log_header,
            'version': self.version,
            'previous_hash': self.previous_hash,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'time': self.time,
            'events_hash': self.events_hash,
            'events': events
        }


class ChainIndex(database.Model):
    __tablename__ = 'chain_indices'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    root_id = Column(Integer, ForeignKey('chain_indices.id'))
    previous_id = Column(Integer, ForeignKey('chain_indices.id'))
    star_log_id = Column(Integer, ForeignKey('star_logs.id'))
    previous_star_log_id = Column(Integer, ForeignKey('star_logs.id'))
    hash = Column(String(64))
    previous_hash = Column(String(64))
    height = Column(Integer)
    chain = Column(Integer)

    def __repr__(self):
        return '<Chain Index %s>' % self.id

    def __init__(self,
                 root_id,
                 previous_id,
                 star_log_id,
                 previous_star_log_id,
                 hash,
                 previous_hash,
                 height,
                 chain):
        self.root_id = root_id
        self.previous_id = previous_id
        self.star_log_id = star_log_id
        self.previous_star_log_id = previous_star_log_id
        self.hash = hash
        self.previous_hash = previous_hash
        self.height = height
        self.chain = chain

    def get_json(self):
        return {
            'hash': self.hash,
            'previous_hash': self.previous_hash,
            'height': self.height
        }


class Chain(database.Model):
    __tablename__ = 'chains'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    height = Column(Integer)
    head_index_id = Column(Integer)
    chain = Column(Integer)
    star_log_id = Column(Integer)

    def __repr__(self):
        return '<Chain %s>' % self.id

    def __init__(self, height, head_index_id, chain, star_log_id):
        self.height = height
        self.head_index_id = head_index_id
        self.chain = chain
        self.star_log_id = star_log_id

    def get_json(self):
        return {
            'height': self.height,
            'chain': self.chain
        }


class Fleet(database.Model):
    __tablename__ = 'fleets'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    hash = Column(String(64))
    public_key = Column(String(392))

    def __repr__(self):
        return '<Fleet %r>' % self.id

    def __init__(self, hash, public_key):
        self.hash = hash
        self.public_key = public_key

    def get_json(self):
        return {
            'hash': self.hash,
            'public_key': self.public_key
        }


class Event(database.Model):
    __tablename__ = 'events'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer)
    model_type_id = Column(Integer)
    fleet_id = Column(Integer, ForeignKey('fleets.id'))
    key = Column(String(64))
    star_system_id = Column(Integer, ForeignKey('star_logs.id'))

    def __repr__(self):
        return '<Event %s>' % self.id

    def __init__(self, key, type_id, model_type_id, fleet_id, star_system_id):
        self.key = key
        self.type_id = type_id
        self.model_type_id = model_type_id
        self.fleet_id = fleet_id
        self.star_system_id = star_system_id

    def get_json(self):
        return {'key': self.key}


class EventSignature(database.Model):
    __tablename__ = 'event_signatures'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer)
    fleet_id = Column(Integer, ForeignKey('fleets.id'))
    hash = Column(String(64))
    signature = Column(String(512))
    time = Column(Integer)
    confirmations = Column(Integer)

    def __repr__(self):
        return '<Event Signature %s>' % self.id

    def __init__(self,
                 type_id,
                 fleet_id,
                 hash,
                 signature,
                 time,
                 confirmations):
        self.type_id = type_id
        self.fleet_id = fleet_id
        self.hash = hash
        self.signature = signature
        self.time = time
        self.confirmations = confirmations

    def get_json(self, fleet_hash, fleet_key, inputs, outputs, index):
        return {
            'index': index,
            'type': util.get_event_type_name(self.type_id),
            'fleet_hash': fleet_hash,
            'fleet_key': fleet_key,
            'inputs': inputs,
            'outputs': outputs,
            'hash': self.hash,
            'signature': self.signature
        }


class EventInput(database.Model):
    __tablename__ = 'event_inputs'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    event_signature_id = Column(Integer, ForeignKey('event_signatures.id'))
    index = Column(Integer)

    def __repr__(self):
        return '<Event %s>' % self.id

    def __init__(self, event_id, event_signature_id, index):
        self.event_id = event_id
        self.event_signature_id = event_signature_id
        self.index = index

    def get_json(self, key):
        return {
            'index': self.index,
            'key': key
        }


class EventOutput(database.Model):
    __tablename__ = 'event_outputs'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'))
    event_signature_id = Column(Integer, ForeignKey('event_signatures.id'))
    index = Column(Integer)

    def __repr__(self):
        return '<Event %s>' % self.id

    def __init__(self, event_id, event_signature_id, index):
        self.event_id = event_id
        self.event_signature_id = event_signature_id
        self.index = index

    def get_json(self, type_name, fleet_hash, key, star_system, model, model_type):
        return {
            'index': self.index,
            'type': type_name,
            'fleet_hash': fleet_hash,
            'key': key,
            'star_system': star_system,
            'model': model,
            'model_type': model_type
        }


class StarLogEventSignature(database.Model):
    __tablename__ = 'star_log_event_signatures'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    event_signature_id = Column(Integer, ForeignKey('event_signatures.id'))
    star_log_id = Column(Integer, ForeignKey('star_logs.id'))
    index = Column(Integer)

    def __repr__(self):
        return '<Starlog Event Signature %s>' % self.id

    def __init__(self, event_signature_id, star_log_id, index):
        self.event_signature_id = event_signature_id
        self.star_log_id = star_log_id
        self.index = index

    def get_json(self):
        return {}


class EventType(database.Model):
    __tablename__ = 'event_types'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    name = Column(String(16))

    def __repr__(self):
        return '<Starlog Event Type %s>' % self.id

    def __init__(self, name):
        self.name = name

    def get_json(self):
        return {}


class EventModelType(database.Model):
    __tablename__ = 'event_model_types'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    name = Column(String(16))

    def __repr__(self):
        return '<Model Type %s>' % self.id

    def __init__(self, name):
        self.name = name

    def get_json(self):
        return {}

class ModuleType(database.Model):
    __tablename__ = 'module_types'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    name = Column(String(16))

    def __repr__(self):
        return '<Module Type %s>' % self.id

    def __init__(self, name):
        self.name = name

    def get_json(self):
        return {}

class EventModel(database.Model):
    __tablename__ = 'event_models'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer)
    model_id = Column(Integer)
    type_id = Column(Integer)

    def __repr__(self):
        return '<Event Model %s>' % self.id

    def __init__(self, event_id, model_id, type_id):
        self.event_id = event_id
        self.model_id = model_id
        self.type_id = type_id

    def get_json(self):
        return {}

class HullBlueprint(database.Model):
    __tablename__ = 'hull_blueprints'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    hash = Column(String(64))
    mass_limit = Column(Integer)
    fleet_id = Column(Integer, ForeignKey('fleets.id'))

    def __repr__(self):
        return '<Hull Blueprint %s>' % self.id

    def __init__(self, hash, mass_limit, fleet_id):
        self.hash = hash
        self.mass_limit = mass_limit
        self.fleet_id = fleet_id

    def get_json(self):
        return {}


class JumpDriveBlueprint(database.Model):
    __tablename__ = 'jump_drive_blueprints'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    hash = Column(String(64))
    health_limit = Column(Integer)
    mass = Column(Integer)
    distance_scalar = Column(Float)
    fuel_scalar = Column(Float)
    mass_limit = Column(Integer)
    fleet_id = Column(Integer, ForeignKey('fleets.id'))
    
    def __repr__(self):
        return '<Jump Drive Blueprint %s>' % self.id

    def __init__(self, hash, health_limit, mass, distance_scalar, fuel_scalar, mass_limit, fleet_id):
        self.hash = hash
        self.health_limit = health_limit
        self.mass = mass
        self.distance_scalar = distance_scalar
        self.fuel_scalar = fuel_scalar
        self.mass_limit = mass_limit
        self.fleet_id = fleet_id

    def get_json(self):
        return {}


class JumpDrive(database.Model):
    __tablename__ = 'jump_drive_modules'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    blueprint_id = Column(Integer)
    health = Column(Integer)
    index = Column(Integer)
    delta = Column(Boolean)

    def __repr__(self):
        return '<Jump Drive %s>' % self.id

    def __init__(self, blueprint_id, health, delta, index):
        self.blueprint_id = blueprint_id
        self.health = health
        self.delta = delta
        self.index = index

    def get_json(self, blueprint):
        return {
            'blueprint': blueprint,
            'delta': self.delta,
            'health': self.health,
            'index': self.index,
            'module_type': 'jump_drive'
        }

class CargoBlueprint(database.Model):
    __tablename__ = 'cargo_blueprints'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    hash = Column(String(64))
    health_limit = Column(Integer)
    mass = Column(Integer)
    mass_limit = Column(Integer)
    fleet_id = Column(Integer, ForeignKey('fleets.id'))

    def __repr__(self):
        return '<Cargo Blueprint %s>' % self.id

    def __init__(self, hash, health_limit, mass, mass_limit, fleet_id):
        self.hash = hash
        self.health_limit = health_limit
        self.mass = mass
        self.mass_limit = mass_limit
        self.fleet_id = fleet_id

    def get_json(self):
        return {}


class Cargo(database.Model):
    __tablename__ = 'cargo_modules'
    extend_existing = True

    id = Column(Integer, primary_key=True)
    blueprint_id = Column(Integer)
    health = Column(Integer)
    fuel_mass = Column(Integer)
    index = Column(Integer)
    delta = Column(Boolean)

    def __repr__(self):
        return '<Cargo %s>' % self.id

    def __init__(self, blueprint_id, health, delta, fuel_mass, index):
        self.blueprint_id = blueprint_id
        self.health = health
        self.delta = delta
        self.fuel_mass = fuel_mass
        self.index = index

    def get_json(self, blueprint):
        return {
            'blueprint': blueprint,
            'delta': self.delta,
            'health': self.health,
            'contents': {
                'fuel': self.fuel_mass,
            },
            'index': self.index,
            'module_type': 'cargo'
        }

def populate_types(session, type_class, type_names):
    for existing in session.query(type_class).all():
        if existing.name not in type_names:
            raise Exception('Database already contains unrecognized value %s' % existing.name)
        type_names.remove(existing.name)
    for current_type in type_names:
        if current_type == 'unknown':
            continue
        session.add(type_class(current_type))

def initialize_models():
    session = database.session()
    try:
        populate_types(
            session,
            EventType,
            list(util.EVENT_TYPES)
        )
        
        populate_types(
            session,
            EventModelType,
            list(util.EVENT_MODEL_TYPES)
        )

        populate_types(
            session,
            ModuleType,
            list(util.MODULE_TYPES)
        )
        session.commit()

        if session.query(HullBlueprint).filter_by(hash=DEFAULT_HULL['hash']).first() is None:
            session.add(HullBlueprint(DEFAULT_HULL['hash'], DEFAULT_HULL['mass_limit'], None))
        if session.query(CargoBlueprint).filter_by(hash=DEFAULT_CARGO['hash']).first() is None:
            session.add(CargoBlueprint(DEFAULT_CARGO['hash'], DEFAULT_CARGO['health_limit'], DEFAULT_CARGO['mass'], DEFAULT_CARGO['mass_limit'], None))
        if session.query(JumpDriveBlueprint).filter_by(hash=DEFAULT_JUMP_DRIVE['hash']).first() is None:
            session.add(JumpDriveBlueprint(DEFAULT_JUMP_DRIVE['hash'], DEFAULT_JUMP_DRIVE['health_limit'], DEFAULT_JUMP_DRIVE['mass'], DEFAULT_JUMP_DRIVE['distance_scalar'], DEFAULT_JUMP_DRIVE['fuel_scalar'], DEFAULT_JUMP_DRIVE['mass_limit'], None))
        session.commit()
    finally:
        session.close()
