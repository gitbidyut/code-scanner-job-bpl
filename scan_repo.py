import boto3
import json
import os
import sys

runtime = boto3.client("sagemaker-runtime")

ENDPOINT = "credential-scanner-endpoint"

def scan_text(text):
    response = runtime.invoke_endpoint(
    EndpointName=ENDPOINT,
    ContentType="application/octet-stream",
    Accept="application/json",
    Body=content.encode("utf-8")
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
for text in violations:
    print(text)
if violations:
    print("❌ Credential(s) detected:")
    for v in violations:
        print(v)
else:
  print("✅ No credentials detected")