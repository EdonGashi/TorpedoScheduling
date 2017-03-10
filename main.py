'''Program entry'''
import sys
import json
import os.path
import evaluator
from instance import Instance
from solution import find_initial_solution, hill_climb


def _print_solution(instance, solution, matrix):
    timeline = evaluator.create_solution_timeline(instance, solution, matrix)
    desulf_time = evaluator.calculate_desulf_time(solution, matrix)
    total_time = evaluator.calculate_total_time(instance, solution, matrix)
    conflicts, conflict_count, max_conflicts, conflict_map, torpedo_count \
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
    # bf_set = set()
    # for bf, c in enumerate(solution):
    #     print ('BF=', bf, 'C=', c)
    # for conflict in conflicts:
    #     print(conflict)
    #     for time in conflict[1]:
    #         bf_set.add(time[0])
    # for bf_id in bf_set:
    #     print(bf_id, matrix[solution[bf_id]].sparse_list[bf_id].buffer_duration, solution[bf_id])



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
    elif command == 'solution':
        instance = _get_instance()
        solution, matrix = find_initial_solution(instance)
        _print_solution(instance, solution, matrix)
        print('\nOptimizing solution...\n')
        hill_climb(instance, solution, matrix)
        _print_solution(instance, solution, matrix)
    elif command == 'initial_solution':
        instance = _get_instance()
        solution, matrix = find_initial_solution(instance)
        _print_solution(instance, solution, matrix)
    elif command == 'print_initial_solution':
        instance = _get_instance()
        solution, matrix = find_initial_solution(instance)
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
