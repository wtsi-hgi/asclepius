


from multiprocessing import Pool
import logging

class Executor:
    '''
    The execution manager will do the following:
    * It will consume the stream of file-AVU tuples.
    * It will pass this to an execution worker (the pool thereof is either managed by this, or by the overall wrapper...probably the execution manager would be best).
    * Each execution worker will check the current AVUs on said file, then commit the difference (i.e., the new ones) per its input. This will ensure idempotency.
    Remember to use appropriate synchronisation primitives for your multiprocessing so you don't get race conditions on your queue. Ultimately, the end-user interface will be something like:
    metadata-adder --collection ROOT_COLLECTION --config /path/to/config
    '''
    def __init__(self, num_executors):
        self.process_pool = Pool(num_executors)
        self.make_session()
    


    def make_session(self):
        import os
        import ssl
        from irods.session import iRODSSession
        env_file = os.path.expanduser('/nfs/users/nfs_m/mercury/.irods/irods_environment.json')
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None)
        ssl_settings = {'ssl_context': ssl_context}
        with iRODSSession(irods_env_file=env_file, **ssl_settings) as session:
            self.session = session
        
    def get_metadata(self, filepath):
        
        obj = self.session.data_objects.get(filepath)
        return obj.metadata
    

    def execute_plan(self, plan, overwrite = False):
        filepath = plan.data_object
        planned_AVUs = plan.metadata #List of AVUs
        from irods.meta import iRODSMeta
        existing_metadata = self.get_metadata(filepath)
        with self.process_pool as p:
            print(planned_AVUs)
            if overwrite is True:
                for avu in planned_AVUs:
                    new_AVU = iRODSMeta(avu.attribute,avu.value,avu.unit)
                    existing_metadata[avu.attribute] = new_AVU
            else: 
                for avu in planned_AVUs:
                 
                    try:
                        existing_metadata.get_one(avu.attribute)
                    except:
                        new_AVU = iRODSMeta(avu.attribute,avu.value,avu.unit)
                        existing_metadata[avu.attribute] = new_AVU     
        # On close, context manager returns process to pool

        

  



    
