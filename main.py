import argparse

import planner.planner as planner
import executor.executor as executor

parser = argparse.ArgumentParser(description="Apply metadata AVUs to all " +
    "data objects in an iRODS collection.")

parser.add_argument('--config', '-c', nargs='?', default='config.yaml',
    help="Configuration file path.")

parser.add_argument('--including_collections', '-i', action='store_const',
    const=True, default=False, help="Include this flag to apply metadata AVUs" +
    "to collections as well as data objects. ")

parser.add_argument('root_collection', nargs=1,
    help="Path to the root iRODS collection.")

WORKERS = 4

if __name__ == "__main__":
    args = parser.parse_args()
    executor = Executor(WORKERS)

    for plan in planner.generate_avus(args.root_collection[0],
            args.config, args.including_collections):
        executor.execute_plan(plan)
