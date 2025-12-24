import boto3
import json
import os

runtime = boto3.client("sagemaker-runtime")

def scan_file(content):
    response = runtime.invoke_endpoint(
        EndpointName="credential-scanner-endpoint",
        ContentType="application/json",
        Body=json.dumps({"text": content})
    )
    return json.loads(response["Body"].read())

# Example: scan repo files
for root, _, files in os.walk("."):
    for f in files:
        if f.endswith((".py", ".js", ".env", ".yaml", ".tf")):
            with open(os.path.join(root, f)) as file:
                result = scan_file(file.read())
                if result["credential_found"]:
                    raise Exception(f"Credential detected in {f}")
