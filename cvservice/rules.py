import math
import numpy
from cvservice.util import sha256

class Rules(object):

    INTEGER_MAX = 2147483647
    NONCE_MAX = 2147483647
    TARGET_MAX = '00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
    EMPTY_TARGET = '0000000000000000000000000000000000000000000000000000000000000000'

    EVENT_TYPES = [
        'reward',
        'jump',
        'attack',
        'transfer'
    ]

    EVENT_USAGES = [
        'input',
        'output'
    ]

    EVENT_MODEL_TYPES = [
        'vessel'
    ]

    RESOURCE_TYPES = [
        'fuel'
    ]

    MODULE_TYPES = [
        'hull',
        'jump_drive',
        'cargo'
    ]

    def __init__(self, **kwargs):
        self.version = kwargs.get('version', 0)
        self.block_size = kwargs.get('block_size', 1000000)
        self.difficulty_fudge = kwargs.get('difficulty_fudge', 0)
        self.difficulty_duration = kwargs.get('difficulty_duration', 1209600)
        self.difficulty_interval = kwargs.get('difficulty_interval', 10080)
        self.difficulty_start = kwargs.get('difficulty_start', 486604799)
        # TODO: probe reward
        self.probe_reward = kwargs.get('probe_reward', None)
        self.cartesian_digits = kwargs.get('cartesian_digits', 3)
        self.jump_cost_min = kwargs.get('jump_cost_min', 1)
        self.jump_cost_max = kwargs.get('jump_cost_max', 1000)
        self.jump_distance_max = kwargs.get('jump_distance_max', 2048)
        self.blocks_limit_max = kwargs.get('blocks_limit_max', 10)
        self.events_limit_max = kwargs.get('events_limit_max', 10)
        self.event_version = kwargs.get('event_version', 0)

        self.jump_cost_range = self.jump_cost_max - self.jump_cost_min
        
        if self.difficulty_fudge == 0:
            self.target_max = self.TARGET_MAX
        elif not 0 <= self.difficulty_fudge <= 8:
            raise Exception('difficulty_fudge must be a value from 0 to 8 (inclusive')
        else:
            self.target_max = self.TARGET_MAX[self.difficulty_fudge:] + self.TARGET_MAX[:self.difficulty_fudge]

        if not 3 <= self.cartesian_digits <= 21:
            raise Exception('cartesian_digits must be a value from 3 to 21 (inclusive)')
        if not 0 <= self.jump_cost_min:
            raise Exception('jump_cost_min must be equal to or greater than zero')
        if not 0 < self.jump_cost_max:
            raise Exception('jump_cost_max must be greater than zero')
        if self.jump_cost_max <= self.jump_cost_min:
            raise Exception('jump_cost_min must be less than jump_cost_max')
        if self.jump_distance_max <= 0:
            raise Exception('jump_dist_max must be greater than zero')

        blueprints = kwargs.get('blueprints')
        self.default_hull = blueprints['hull']
        self.default_cargo = blueprints['cargo']
        self.default_jump_drive = blueprints['jump_drive']

    def is_genesis_block(self, sha):
        """Checks if the provided hash could only belong to the parent of the genesis block.

        Args:
            sha (str): Hash to check.

        Results:
            bool: True if equal to the hash of the parent of the genesis block's parent.
        """
        return sha == self.EMPTY_TARGET

    def difficulty_from_target(self, target):
        """Calculates the difficulty this target is equal to.
        
        Args:
            target (str): Hex target, stripped of its leading 0x.
        
        Returns:
            str: Packed hex difficulty of the target, stripped of its leading 0x.
        """
        # TODO: Cleanup shitwise operators that use string transformations, they're ugly... though they do work...
        stripped = target.lstrip('0')

        # If we stripped too many zeros, add one back.
        if len(stripped) % 2 == 0:
            stripped = '0' + stripped

        count = len(stripped) / 2
        stripped = stripped[:6]

        # If we're past the max value allowed for the mantissa, truncate it further and increase the exponent.
        if 0x7fffff < int(stripped, 16):
            stripped = '00' + stripped[0:4]
            count += 1

        result = hex(count)[2:] + stripped

        # Negative number switcharoo
        if 0x00800000 & int(result, 16):
            result = hex(count + 1)[2:] + '00' + stripped[:4]
        # # Lazy max number check...
        # if 0x1d00ffff < int(result, 16):
        #     result = '1d00ffff'
        return result


    def is_difficulty_changing(self, height):
        """Checks if it's time to recalculate difficulty.
        
        Args:
            height (int): Height of an entry in the chain.
        
        Returns:
            bool: True if a difficulty recalculation should take place.
        """
        return (height % self.difficulty_interval) == 0
    
    def calculate_difficulty(self, difficulty, duration):
        """Takes the packed integer difficulty and the duration of the last interval to calculate the new difficulty.
        
        Args:
            difficulty (int): Packed int format of the last difficulty.
            duration (int): Seconds elapsed since the last time difficulty was calculated.
        
        Returns:
            int: Packed int format of the next difficulty.
        """
        if duration < self.difficulty_duration / 4:
            duration = self.difficulty_duration / 4
        elif duration > self.difficulty_duration * 4:
            duration = self.difficulty_duration * 4

        limit = long(self.target_max, 16)
        result = long(self.unpack_bits(difficulty), 16)
        result *= duration
        result /= self.difficulty_duration

        if limit < result:
            result = limit

        return int(self.difficulty_from_target(hex(result)[2:]), 16)

    def unpack_bits(self, difficulty, strip=False):
        """Unpacks int difficulty into a target hex.
        Args:
            difficulty (int): Packed int representation of a difficulty.
        
        Returns:
            str: Hex value of a target hash equal to this difficulty, stripped of its leading 0x.
        """
        sha = hex(difficulty)[2:]
        digit_count = int(sha[:2], 16)

        if digit_count == 0:
            digit_count = 3

        digits = []
        if digit_count == 29:
            digits = [sha[4:6], sha[6:8]]
        else:
            digits = [sha[2:4], sha[4:6], sha[6:8]]

        digit_count = min(digit_count, 28)
        significant_count = len(digits)

        leading_padding = 28 - digit_count
        trailing_padding = 28 - (leading_padding + significant_count)

        base256 = ''

        for i in range(0, leading_padding + 4):
            base256 += '00'
        for i in range(0, significant_count):
            base256 += digits[i]
        for i in range(0, trailing_padding):
            base256 += '00'

        if 0 < self.difficulty_fudge:
            base256 = base256[self.difficulty_fudge:] + base256[:self.difficulty_fudge]
        return base256.rstrip('0') if strip else base256
    
    def get_jump_cost(self, origin_hash, destination_hash):
        """Gets the fuel cost for this jump.
        Args:
            origin_hash (str): The starting hash of the jump.
            destination_hash (str): The ending hash of the jump.
        
        Returns:
            int: The fuel requirement for this jump.
        """
        distance = self.get_distance(origin_hash, destination_hash)
        if self.jump_distance_max < distance:
            return -1
        elif self.jump_distance_max == distance:
            return self.jump_cost_max
        # Scalar is x^2
        scalar = math.sqrt(distance / self.jump_distance_max)
        return int(math.ceil(self.jump_cost_min + (self.jump_cost_range * scalar)))

    def get_cartesian_minimum(self):
        """Gets the (x, y, z) position of the minimum possible system.
        
        Returns:
            array: A list containing the (x, y, z) position.
        """
        return numpy.array([0, 0, 0])

    def get_cartesian_maximum(self):
        """Gets the (x, y, z) position of the maximum possible system.
        
        Returns:
            array: A list containing the (x, y, z) position.
        """
        max_value = pow(16, self.cartesian_digits)
        return numpy.array([max_value, max_value, max_value])

    def get_cartesian(self, system_hash):
        """Gets the (x, y, z) position of the specified system.
        Args:
            system_hash (str): The system's Sha256 hash.
        
        Returns:
            numpy.array: A list containing the (x, y, z) position.
        """
        cartesian_hash = sha256('%s%s' % ('cartesian', system_hash))
        total_digits = self.cartesian_digits * 3
        cartesian = cartesian_hash[-total_digits:]
        return numpy.array(
            [
                int(cartesian[:self.cartesian_digits], 16), 
                int(cartesian[self.cartesian_digits:-self.cartesian_digits], 16), 
                int(cartesian[(2*self.cartesian_digits):], 16)
            ]
        )

    def get_distance(self, origin_hash, destination_hash):
        """Gets the distance between the specified systems in cartesian space.
        Args:
            origin_hash (str): The origin system's Sha256 hash.
            destination_hash (str): The destination system's Sha256 hash.
        
        Returns:
            float: The distance between the two systems.
        """
        origin_pos = self.get_cartesian(origin_hash)
        destination_pos = self.get_cartesian(destination_hash)
        return int(math.ceil(numpy.linalg.norm(origin_pos - destination_pos)))