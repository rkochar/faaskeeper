import json

from functions.gcp.control.distributor_queue import DistributorQueuePubSub

def main():
    writerQueue = DistributorQueuePubSub("top-cascade-392319", "faasWriter") # worker-queue

    payload = {
    "op": "create_node",
        "path": "/root20",
        "data": "ImRhdGF2ZXIxIg==",#base64.b64encoded
        "session_id": "fa3a0cf0", # is defined in the client library
        "timestamp": "fa3a0cf0-2",
        "flags": "0",
        # "event_id": "7c75aaaf0413f5ef82320e05f689cb38"
    }

    data = json.dumps(payload).encode()

    future = writerQueue.publisher_client.publish(writerQueue.topic_path, data= data, ordering_key= "fa3a0cf0")
    print(future.result())

if __name__ == "__main__":
    main()

    1691032414354658