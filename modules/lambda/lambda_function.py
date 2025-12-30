import boto3
import os
import json 

iam = boto3.client("iam")
sns = boto3.client("sns")

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:361509912577:credential-scan-alerts-bpl"

def send_alert(message):
    if not SNS_TOPIC_ARN:
        print("SNS_TOPIC_ARN not set")
        return

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="🚨 Credential Disabled by CI/CD Scanner",
        Message=json.dumps(message, indent=2)
    )

def get_username_from_access_key(access_key_id):
    paginator = iam.get_paginator("list_users")

    for page in paginator.paginate():
        for user in page["Users"]:
            keys = iam.list_access_keys(UserName=user["UserName"])
            for key in keys["AccessKeyMetadata"]:
                if key["AccessKeyId"] == access_key_id:
                    return user["UserName"]
    return None


def lambda_handler(event, context):
    access_key_id = event.get("access_key_id")
    source_file= event.get("source_file")
    if not access_key_id:
        raise ValueError("access_key_id missing in event")

    username = get_username_from_access_key(access_key_id)

    if not username:
        print(f"Access key not found: {access_key_id}")
        return {"status": "not_found"}
    
    print(f"Disabling access key {access_key_id} for user {username}")
    
    iam.update_access_key(
        UserName=username,
        AccessKeyId=access_key_id,
        Status="Inactive"
    )

    
    alert = {
        "status": "DISABLED",
        "user": username,
        "access_key": access_key_id,
        "source_file": source_file
    }

    #print(alert)
    send_alert(alert)

    return alert
    # return {
    #     "status": "disabled",
    #     "user": username,
    #     "access_key": access_key_id
    # }

