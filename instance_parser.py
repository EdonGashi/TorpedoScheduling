'''Provides utilities for parsing problem instances'''


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


def parse(lines, suppress_missing_props=False):
    '''Parse string lines into a problem instance.
    Returns a dictionary (**PROBLEM_PROPERTIES, bfSchedules, converterSchedules)
    '''

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

    if not suppress_missing_props:
        for prop in PROBLEM_PROPERTIES:
            if not prop in properties:  # Check for missing properties
                raise Exception('Missing property %s' % prop)

    properties[BF_SCHEDULES] = bf_schedules
    properties[CONVERTER_SCHEDULES] = converter_schedules
    return properties
