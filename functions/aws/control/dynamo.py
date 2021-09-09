import base64
from typing import Set, Union

import boto3
from boto3.dynamodb.types import TypeSerializer

from faaskeeper.node import Node, NodeDataType

from .storage import Storage


class DynamoStorage(Storage):
    def __init__(self, table_name: str, key_name: str):
        super().__init__(table_name)
        self._dynamodb = boto3.client("dynamodb")
        self._type_serializer = TypeSerializer()
        self._key_name = key_name

    def write(self, key: str, data: Union[dict, bytes]):
        """DynamoDb write"""

        return self._dynamodb.put_item(
            TableName=self.storage_name,
            Item=data,
            ExpressionAttributeNames={"#P": self._key_name},
            ConditionExpression="attribute_not_exists(#P)",
            ReturnConsumedCapacity="TOTAL",
        )

    def update(self, key: str, data: dict):
        """DynamoDb update"""

        def get_object(obj: dict):
            return next(iter(obj.values()))

        self._dynamodb.update_item(
            TableName=self.storage_name,
            Key={self._key_name: {"S": key}},
            ConditionExpression="attribute_exists(#P)",
            UpdateExpression="SET #D = :data ADD version :inc",
            ExpressionAttributeNames={"#D": "data", "#P": "path"},
            ExpressionAttributeValues={
                ":version": {"N": get_object(data["version"])},
                ":inc": {"N": "1"},
                ":data": {"B": base64.b64decode(get_object(data["data"]))},
            },
            ReturnConsumedCapacity="TOTAL",
        )

    # def _toSchema(self, node: Node):
    #    # FIXME: pass epoch counter value
    #    schema = {
    #        "path": {"S": node.path},
    #        "data": {"B": node.data},
    #        "mFxidSys": node.modified.system.version,
    #        "mFxidEpoch": {"NS": ["0"]},
    #    }
    #    if node.created.system:
    #        schema = {
    #            **schema,
    #            "cFxidSys": node.created.system.version,
    #            "cFxidEpoch": {"NS": ["0"]},
    #        }
    #    return schema
    def _toSchema(self, node: Node):
        # FIXME: pass epoch counter value
        schema = {
            ":data": {"B": node.data},
            ":mFxidSys": node.modified.system.version,
            ":mFxidEpoch": {"NS": ["0"]},
        }
        return schema

    def update_node(self, node: Node, updates: Set[NodeDataType]):

        update_expr = "SET "
        schema: dict = {}
        attribute_names = {"#P": "path"}
        # FIXME: pass epoch counter value
        if NodeDataType.DATA in updates:
            schema[":data"] = {"B": node.data}
            update_expr = f"{update_expr} #D = :data,"
            attribute_names["#D"] = "data"
        if NodeDataType.CREATED in updates:
            schema = {
                **schema,
                ":cFxidSys": node.created.system.version,
                ":cFxidEpoch": {"NS": ["0"]},
            }
            update_expr = f"{update_expr} cFxidSys = :createdStamp,"
        if NodeDataType.MODIFIED in updates:
            schema = {
                **schema,
                ":mFxidSys": node.modified.system.version,
                ":mFxidEpoch": {"NS": ["0"]},
            }
            update_expr = f"{update_expr} mFxidSys = :modifiedStamp,"
        if NodeDataType.CHILDREN in updates:
            schema[":children"] = self._type_serializer.serialize(node.children)
            update_expr = f"{update_expr} children = :children,"
        # strip traling comma - boto3 will not accept that
        update_expr = update_expr[:-1]

        self._dynamodb.update_item(
            TableName=self.storage_name,
            Key={self._key_name: {"S": node.path}},
            ConditionExpression="attribute_exists(#P)",
            UpdateExpression=update_expr,
            ExpressionAttributeNames=attribute_names,
            ExpressionAttributeValues=schema,
            ReturnConsumedCapacity="TOTAL",
        )

    def read(self, key: str):
        """DynamoDb read"""

        return self._dynamodb.get_item(
            TableName=self.storage_name, Key={self._key_name: {"S": key}}
        )

    def delete(self, key: str):
        """DynamoDb delete"""

        self._dynamodb.delete_item(
            TableName=self.storage_name,
            Key={self._key_name: {"S": key}},
            ReturnConsumedCapacity="TOTAL",
        )

    @property
    def errorSupplier(self):
        """DynamoDb exceptions"""

        return self._dynamodb.exceptions
