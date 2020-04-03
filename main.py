import argparse

import planner.planner as planner
from executor.executor import Executor
import core.irods_wrapper as irods_wrapper
import json


def run(root_collection, config, include_collections=False, overwrite=False, num_workers=4, catalogue_file='catalogue.txt', progress_file='progress.txt', resume = False):
    irods_session = irods_wrapper.create_session()
    if not resume:
        catalogue = irods_wrapper.get_irods_catalogue(root_collection)
        with open(catalogue_file, 'w+') as cf:
            json.dump(catalogue, cf)
    else:
        with open(catalogue_file, 'r') as cf:
            catalogue = json.load(cf)
    executor = Executor(irods_session, num_workers)
    with open(progress_file, 'a+') as pf:
        for plan in planner.generate_plans(catalogue, config, progress_file,
                resume, include_collections):
            executor.execute_plan(plan, overwrite)
            pf.write(plan.path)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Apply metadata AVUs to all " +
        "data objects in an iRODS collection.")
    parser.add_argument('--config', '-c', nargs='?', default='config.yaml',
        help="Configuration file path.")
    parser.add_argument('--including_collections', '-i', action='store_const',
        const=True, default=False, help="Include this flag to apply metadata" +
        "AVUs to collections as well as data objects. ")
    parser.add_argument('--overwrite', '-o', action='store_const', const=True,
        default=False, help="Whether to overwrite existing AVUs in case of" + "conflict")
    parser.add_argument('--catalogue_file', '-f' nargs=1,
        default="catalogue.txt", help="Path to the file which logs the" + "catalogue.")
    parser.add_argument('--progress_file', '-p', nargs=1,
        default = "progress.txt", help="Path to the file which logs progress.")
    parser.add_argument('--resume', '-r', action='store_const', const=True,
        default=False, help="Whether to restart")
    parser.add_argument('root_collection', nargs=1,
        help="Path to the root iRODS collection.")
    args = parser.parse_args()
    WORKERS = 4
    run(args.root_collection[0], args.config, args.including_collections, args.overwrite, WORKERS, args.catalogue_file, args.progress_file, restart)
