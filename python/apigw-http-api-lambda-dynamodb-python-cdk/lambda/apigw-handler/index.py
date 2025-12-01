# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

import boto3
import os
import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb_client = boto3.client("dynamodb")


def log_event(level, message, **kwargs):
    """Structured logging helper"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        **kwargs
    }
    logger.info(json.dumps(log_entry))


def handler(event, context):
    request_id = context.request_id
    source_ip = event.get("requestContext", {}).get("identity", {}).get("sourceIp")
    http_method = event.get("httpMethod")
    
    log_event(
        "INFO",
        "Processing request",
        request_id=request_id,
        source_ip=source_ip,
        http_method=http_method,
    )
    
    table = os.environ.get("TABLE_NAME")
    log_event("INFO", "Loaded table name", table_name=table, request_id=request_id)
    
    if event.get("body"):
        item = json.loads(event["body"])
        log_event("INFO", "Received payload", request_id=request_id, has_payload=True)
        year = str(item["year"])
        title = str(item["title"])
        id = str(item["id"])
        dynamodb_client.put_item(
            TableName=table,
            Item={"year": {"N": year}, "title": {"S": title}, "id": {"S": id}},
        )
        log_event("INFO", "Data inserted successfully", request_id=request_id, item_id=id)
        message = "Successfully inserted data!"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": message}),
        }
    else:
        log_event("INFO", "No payload received, using default data", request_id=request_id)
        default_id = str(uuid.uuid4())
        dynamodb_client.put_item(
            TableName=table,
            Item={
                "year": {"N": "2012"},
                "title": {"S": "The Amazing Spider-Man 2"},
                "id": {"S": default_id},
            },
        )
        log_event("INFO", "Default data inserted successfully", request_id=request_id, item_id=default_id)
        message = "Successfully inserted data!"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": message}),
        }
