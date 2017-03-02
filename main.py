'''Program entry'''
import sys
import json
import evaluator
from instance import Instance
from solution import find_initial_solution, create_timeline


def _print_solution(torpedo_count, desulf_time, cost, gain):
    print('Torpedo count: {}'.format(torpedo_count))
    print('Desulf time: {}'.format(desulf_time))
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
    if command == 'echo_ins':   # Parse and echo same instance for tesing
        print(repr(_get_instance()))
    elif command == 'parse':    # Parse problem instance
        print(json.dumps(_get_instance().get_properties(),
                         indent=4, separators=(',', ': ')))
    elif command == 'initial_solution':
        problem_instance = _get_instance()
        (solution, _, matrix) = find_initial_solution(problem_instance)
        timeline = create_timeline(problem_instance, solution, matrix)
        torpedo_count = evaluator.count_torpedoes(timeline)
        desulf_time = evaluator.calculate_desulf_time(solution, matrix)
        cost = evaluator.evaluate_solution(
            problem_instance, torpedo_count, desulf_time)
        gain = evaluator.evaluate_gain(problem_instance, cost)
        # print(solution)
        _print_solution(torpedo_count, desulf_time, cost, gain)
    else:
        print('Usage: arg1=command arg2=problem instance)')
        return

if __name__ == '__main__':
    main(sys.argv[1:])
