


from multiprocessing import Pool
from irods.meta import iRODSMeta
import core.irods_wrapper as irods_wrapper

class Executor:
    '''
    The execution manager will do the following:
    * It will consume the stream of file-AVU tuples.
    * It will pass this to an execution worker (the pool thereof is either managed by this, or by the overall wrapper...probably the execution manager would be best).
    * Each execution worker will check the current AVUs on said file, then commit the difference (i.e., the new ones) per its input. This will ensure idempotency.
    Remember to use appropriate synchronisation primitives for your multiprocessing so you don't get race conditions on your queue. Ultimately, the end-user interface will be something like:
    metadata-adder --collection ROOT_COLLECTION --config /path/to/config
    '''
    def __init__(self, irods_session, num_executors):
        self.process_pool = Pool(num_executors)
        self.session = irods_session


    def execute_plan(self, plan, overwrite = False, refresh = False):
        filepath = plan.path
        planned_AVUs = plan.metadata #List of AVUs
        is_collection = plan.is_collection

        existing_metadata = irods_wrapper.get_metadata(self.session, filepath, is_collection)
        with self.process_pool as p: # On close, context manager returns process to pool
            print(f"Filepath: {filepath} AVUs: {planned_AVUs}")

            if refresh:
                for avu in existing_metadata.items():
                    existing_metadata.remove(avu)
                for avu in planned_AVUs:
                    if avu.attribute:
                        new_AVU = iRODSMeta(avu.attribute,avu.value,avu.unit)
                        sexisting_metadata[avu.attribute] = new_AVU
                return 

            if overwrite:
                for avu in planned_AVUs:

                    try:
                        existing_AVU = existing_metadata.get_one(avu.attribute)
                        if existing_AVU.value != avu.value or existing_AVU.units != avu.unit:
                            new_AVU = iRODSMeta(avu.attribute,avu.value,avu.unit)
                            existing_metadata[avu.attribute] = new_AVU 
                    except:
                        if avu.attribute:
                            new_AVU = iRODSMeta(avu.attribute,avu.value,avu.unit)
                            existing_metadata[avu.attribute] = new_AVU 
                return

            if not refresh and not overwrite:
                for avu in planned_AVUs:
                    try:
                        existing_metadata.get_one(avu.attribute)
                    except:
                        new_AVU = iRODSMeta(avu.attribute,avu.value,avu.unit)
                        if avu.attribute:
                            existing_metadata[avu.attribute] = new_AVU
