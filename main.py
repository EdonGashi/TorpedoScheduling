'''Program entry'''
import sys
import json
import os.path
import evaluator
from instance import Instance
from solution import find_initial_solution, hill_climb, ConflictTimeline, resolve_conflicts


def _print_solution(instance, solution, matrix, timeline, conflicts, torpedo_count):
    desulf_time = evaluator.calculate_desulf_time(solution, matrix)
    total_time = evaluator.calculate_total_time(instance, solution, matrix)
    cost = evaluator.evaluate_solution(instance, torpedo_count, desulf_time)
    gain = evaluator.evaluate_gain(instance, cost)
    print('Torpedo count: {}'.format(torpedo_count))
    print('Desulf time: {}'.format(desulf_time))
    print('Total time: {}'.format(total_time))
    print('Conflicts: {}'.format(conflicts))
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
    elif command == 'solve':
        print('Parsing instance...')
        instance = _get_instance()
        print('Finding initial solution...')
        solution, matrix = find_initial_solution(instance)
        print('Optimizing solution...')
        timeline = hill_climb(instance, solution, matrix)
        conflicts, torpedo_count = timeline.count_conflicts()
        if sum(conflicts) > 0:
            print('Resolving conflicts...')
            resolve_conflicts(instance, solution, matrix)
            timeline = ConflictTimeline.create(instance, solution, matrix)
            conflicts, torpedo_count = timeline.count_conflicts()
        print('Evaluating solution...')
        _print_solution(instance, solution, matrix,
                        timeline, conflicts, torpedo_count)
    elif command == 'initial_solution':
        print('Parsing instance...')
        instance = _get_instance()
        print('Finding initial solution...')
        solution, matrix = find_initial_solution(instance)
        print('Evaluating initial solution...')
        timeline = ConflictTimeline.create(instance, solution, matrix)
        conflicts, torpedo_count = timeline.count_conflicts()
        _print_solution(instance, solution, matrix,
                        timeline, conflicts, torpedo_count)
    elif command == 'print_solution':
        instance = _get_instance()
        solution, matrix = find_initial_solution(instance)
        hill_climb(instance, solution, matrix)
        resolve_conflicts(instance, solution, matrix)
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
            print(converter.as_tuple())
    elif command == 'echo_domain':
        instance = _get_instance()
        matrix = instance.create_adjacency_matrix()
        for converter_id, schedule_map in enumerate(matrix):
            print(converter_id, [(s.bf_id, s.duration)
                                 for s in schedule_map.sorted_list])
    else:
        print('Usage: arg1=command arg2=problem instance)')
        return

if __name__ == '__main__':
    main(sys.argv[1:])
