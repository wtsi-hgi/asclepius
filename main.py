import argparse

import planner.planner as planner
from executor.executor import Executor
import core.irods_wrapper as irods_wrapper


def run(root_collection, config, include_collections=False, overwrite=False, num_workers=4):
    irods_session = irods_wrapper.create_session()
    executor = Executor(irods_session, num_workers)
    for plan in planner.generate_plans(root_collection, config,
            include_collections):
        executor.execute_plan(plan, overwrite)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Apply metadata AVUs to all " +
    "data objects in an iRODS collection.")
    parser.add_argument('--config', '-c', nargs='?', default='config.yaml',
    help="Configuration file path.")
    parser.add_argument('--including_collections', '-i', action='store_const',
    const=True, default=False, help="Include this flag to apply metadata AVUs" +
    "to collections as well as data objects. ")
    parser.add_argument('--overwrite', '-o',nargs=1,
    help="Whether to overwrite existing AVUs in case of conflict", default=False)
    parser.add_argument('root_collection', nargs=1,
    help="Path to the root iRODS collection.")
    args = parser.parse_args()
    WORKERS = 4
    run(args.root_collection[0], args.config, args.including_collections, args.overwrite, WORKERS)
