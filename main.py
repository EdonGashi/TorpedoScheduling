'''Program entry'''
import sys
import json
from instance_parser import parse


def main(argv):
    '''Main entry, argv = [command, problem instance]'''

    if len(argv) < 2:
        print('Provide command line arguments (arg1 = command, arg2 = problem instance)')
        return

    command = argv[0]
    if command == 'parse':    # Parse problem instance
        with open(argv[1]) as file:
            problem_instance = parse(file.readlines())
            print(json.dumps(problem_instance, indent=4, separators=(',', ': ')))
    elif command == '':
        pass

if __name__ == '__main__':
    main(sys.argv[1:])
