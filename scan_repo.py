import boto3
import json
import os
import sys

runtime = boto3.client("sagemaker-runtime")

ENDPOINT = "credential-scanner-endpoint"

def scan_text(text):
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT,
        ContentType="application/json",
        Body=json.dumps({"text": text})
    )
    return json.loads(response["Body"].read())

def should_scan(filename):
    return filename.endswith((".py"))

violations = []

for root, _, files in os.walk("."):
    for file in files:
        if should_scan(file):
            path = os.path.join(root, file)
            with open(path, "r", errors="ignore") as f:
                result = scan_text(f.read())
                if result.get("credential_found"):
                    violations.append(path)

if violations:
    print("❌ Credential(s) detected:")
    for v in violations:
        print(v)
    #sys.exit(1)

print("✅ No credentials detected")
