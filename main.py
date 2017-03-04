'''Program entry'''
import sys
import json
import evaluator
import os.path
from instance import Instance
from solution import find_initial_solution


def _print_solution(instance, solution, matrix):
    timeline = evaluator.create_solution_timeline(instance, solution, matrix)
    torpedo_count = evaluator.calculate_torpedo_count(timeline)
    desulf_time = evaluator.calculate_desulf_time(solution, matrix)
    total_time = evaluator.calculate_total_time(instance, solution, matrix)
    conflicts, conflict_count, max_conflicts, conflict_map \
        = evaluator.calculate_conflict_count(instance, timeline)
    cost = evaluator.evaluate_solution(
        instance, torpedo_count, desulf_time)
    gain = evaluator.evaluate_gain(instance, cost)
    print('Torpedo count: {}'.format(torpedo_count))
    print('Desulf time: {}'.format(desulf_time))
    print('Total time: {}'.format(total_time))
    print('Conflict time slots: {}'.format(len(conflicts)))
    print('Conflict count: {}'.format(conflict_count))
    print('Highest conflict count: {}'.format(max_conflicts))
    print('Conflict distribution: {}'.format(conflict_map))
    print('Cost evaluation: {}'.format(cost))
    print('Gain evaluation: {}'.format(gain))


def main(argv):
    '''Main entry, argv = [command, problem instance]'''

    if len(argv) < 2:
        print('Usage: arg1=command arg2=problem instance)')
        return

    def _get_instance():
        with open(argv[1]) as file:
            return Instance.parse(file.readlines())

    command = argv[0]
    if command == 'echo_ins':   # Parse and echo same instance for tesing.
        print(repr(_get_instance()))
    elif command == 'parse':    # Parse problem instance
        print(json.dumps(_get_instance().get_properties(),
                         indent=4, separators=(',', ': ')))
    elif command == 'initial_solution':
        instance = _get_instance()
        solution, stack, matrix = find_initial_solution(instance)
        _print_solution(instance, solution, matrix)
    elif command == 'print_initial_solution':
        instance = _get_instance()
        solution, stack, matrix = find_initial_solution(instance)
        runs, torpedoes = evaluator.calculate_solution_runs(
            instance, solution, matrix)
        print(os.path.basename(argv[1]))
        print('TeamsID=')
        print('nbTorpedoes={}'.format(len(torpedoes)))
        print()
        for run in runs:
            print(run)
    elif command == 'echo_converters':
        instance = _get_instance()
        for converter in instance.converter_schedules:
            print(converter)
    else:
        print('Usage: arg1=command arg2=problem instance)')
        return

if __name__ == '__main__':
    main(sys.argv[1:])
