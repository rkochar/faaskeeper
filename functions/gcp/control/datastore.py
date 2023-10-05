from .storage import Storage
# from google.cloud import firestore_admin_v1
from google.cloud import datastore
import google.cloud.exceptions

class DataStoreStorage(Storage):
    def __init__(self, kind_name: str) -> None:
        super().__init__(kind_name)
        self.client = datastore.Client()
        assert self.client is not None
        
    @property
    def errorSupplier(self):
        return google.cloud.exceptions

    def write(self):
        pass
        

    def update(self):
        pass

    def read(self, path: str):
        assert self.client is not None
        node_key = self.client.key(self.storage_name, path)
        node_info = self.client.get(node_key)

        return node_info

    def delete(self):
        pass

    def _toSchema(self):
        pass

    def update_node(self):
        pass