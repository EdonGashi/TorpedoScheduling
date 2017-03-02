'''Evaluates solutions'''
from instance import Instance


def evaluate_solution(instance: Instance, torpedo_count, desulf_time):
    '''Calculates the evaluation function for the solution parameters.'''
    return torpedo_count + desulf_time \
        / (4 * len(instance.converter_schedules) * instance.dur_desulf)


def evaluate_gain(instance: Instance, cost):
    '''Evaluates gain'''
    return len(instance.bf_schedules) + 1 - cost


def calculate_desulf_time(solution, matrix):
    '''Calculate total desulf time for a solution.'''
    desulf = 0
    for (bf_id, converter_id) in enumerate(solution):
        if converter_id != -1:
            desulf += matrix[converter_id].sparse_list[bf_id].desulf_duration
    return desulf


def count_torpedoes(timeline):
    '''Calculate the maximum number of torpedoes in a timeline.'''
    max_value = 0
    for slot in timeline:
        max_value = max(max_value, len(slot))
    return max_value
