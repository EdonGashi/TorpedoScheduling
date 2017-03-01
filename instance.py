'''Provides utilities for parsing and modelling problem instances.'''
import re

PROBLEM_PROPERTIES = [
    'durBF',
    'durDesulf',
    'durConverter',
    'nbSlotsFullBuffer',
    'nbSlotsDesulf',
    'nbSlotsConverter',
    'ttBFToFullBuffer',
    'ttFullBufferToDesulf',
    'ttDesulfToConverter',
    'ttConverterToEmptyBuffer',
    'ttEmptyBufferToBF',
    'ttBFEmergencyPitEmptyBuffer'
]

BF_SCHEDULES = 'bfSchedules'
CONVERTER_SCHEDULES = 'converterSchedules'


def camel_to_snake(name):
    '''Convert a string from camel case to snake case.'''
    expr = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', expr).lower()


class BFSchedule:
    '''Represents a blast furnace schedule'''

    def __init__(self, schedule_id, time, sulf_level):
        self.schedule_id = schedule_id
        self.time = time
        self.sulf_level = sulf_level

    def __repr__(self):
        return f'BF {self.schedule_id} {self.time} {self.sulf_level}'


class ConverterSchedule:
    '''Represents a converter schedule'''

    def __init__(self, schedule_id, time, max_sulf_level):
        self.schedule_id = schedule_id
        self.time = time
        self.max_sulf_level = max_sulf_level

    def __repr__(self):
        return f'C {self.schedule_id} {self.time} {self.max_sulf_level}'


class Instance:
    '''Models a problem instance.'''

    @staticmethod
    def parse(lines):
        '''Parse string lines into a new problem instance.'''

        bf_schedules = []
        converter_schedules = []
        properties = dict()

        def parse_tuple(expr):
            '''Parse integers from string "X NUM NUM NUM"'''
            expr_list = expr.split()
            return (int(expr_list[1]), int(expr_list[2]), int(expr_list[3]))

        for line in lines:
            if line.startswith('BF '):      # BF NUM NUM NUM
                bf_schedules.append(parse_tuple(line))
            elif line.startswith('C '):     # C NUM NUM NUM
                converter_schedules.append(parse_tuple(line))
            elif '=' in line:               # prop=NUM
                expr_list = line.split('=')
                properties[expr_list[0]] = int(expr_list[1])

        properties[BF_SCHEDULES] = bf_schedules
        properties[CONVERTER_SCHEDULES] = converter_schedules
        return Instance(properties)

    def __init__(self, properties):
        props_dict = dict()
        for prop in PROBLEM_PROPERTIES + [BF_SCHEDULES, CONVERTER_SCHEDULES]:
            if prop not in properties:  # Check for missing properties
                raise Exception('Missing property %s' % prop)
            else:
                setattr(self, camel_to_snake(prop), properties[prop])
                props_dict[prop] = properties[prop]
        self._properties = props_dict

        # Convert tuples to schedule objects
        self.bf_schedules = [BFSchedule(*schedule_tuple)
                             for schedule_tuple in self.bf_schedules]
        self.converter_schedules = [ConverterSchedule(*schedule_tuple)
                                    for schedule_tuple in self.converter_schedules]

    def get_properties(self):
        '''Returns the raw properties dictionary'''
        return self._properties

    def __repr__(self):
        result = ''
        for prop in PROBLEM_PROPERTIES:
            result += f'{prop}={self._properties[prop]}\n'
        for schedule in self.bf_schedules:
            result += repr(schedule) + '\n'
        for schedule in self.converter_schedules:
            result += repr(schedule) + '\n'
        return result
