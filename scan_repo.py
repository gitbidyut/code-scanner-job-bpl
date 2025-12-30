import os
import sys
import json
import re
import boto3

# =========================
# Configuration
# =========================
ENDPOINT_NAME = "credential-scanner-endpoint"
LAMBDA_NAME = "lambda_scanning-function"

REGION = "us-east-1"
THRESHOLD = 0.80

# Ignore rules
IGNORE_EXTENSIONS = {
    ".tf", ".tfvars", ".yml", ".yaml", ".md", ".txt"
}

IGNORE_DIRS = {
    ".git", ".terraform", "test", "tests", "__pycache__", "node_modules"
}

IGNORE_FILES = {
    "scan_repo.py",
    "submit_training.py"
}

# AWS Access Key regex
AWS_ACCESS_KEY_REGEX = r"(AKIA|ASIA)[0-9A-Z]{16}"

# =========================
# AWS Clients
# =========================
runtime = boto3.client("sagemaker-runtime", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

print("🔍 Starting credential scan using SageMaker endpoint...")
print(f"📡 Endpoint: {ENDPOINT_NAME}")

# =========================
# Helper functions
# =========================
def should_ignore(path):
    filename = os.path.basename(path)
    dirname = os.path.basename(os.path.dirname(path))
    ext = os.path.splitext(path)[1]

    if filename in IGNORE_FILES:
        return True
    if dirname in IGNORE_DIRS:
        return True
    if ext in IGNORE_EXTENSIONS:
        return True

    return False


def invoke_remediation(access_key_id, file_path):
    payload = {
        "access_key_id": access_key_id,
        "source_file": file_path,
        "reason": "Credential detected in repository scan"
    }

    lambda_client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="Event",  # async
        Payload=json.dumps(payload)
    )

    print(f"🔒 Remediation triggered for key: {access_key_id}")
    return access_key_id, file_path

def scan_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Extract access key first (fast fail)
    match = re.search(AWS_ACCESS_KEY_REGEX, content)
    if not match:
        return None, None, None

    access_key_id = match.group(0)

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/octet-stream",
        Accept="application/json",
        Body=content.encode("utf-8")
    )

    result = json.loads(response["Body"].read().decode("utf-8"))
    return access_key_id, result["prediction"], result["confidence"]


# =========================
# Main logic
# =========================
def main():
    violations = []

    for root, _, files in os.walk(os.getcwd()):
        for name in files:
            path = os.path.join(root, name)

            if should_ignore(path):
                continue

            result = scan_file(path)
            if not result or result[0] is None:
                continue

            access_key_id, pred, conf = result
            print(f"➡️ {path} | key={access_key_id} | confidence={conf:.3f}")

            if pred == 1 and conf >= THRESHOLD:
                print(f"❌ Credential detected in {path}")

                access_key_id, file_path=invoke_remediation(access_key_id, path)

                violations.append({
                    "file": file_path,
                    "access_key": access_key_id,
                    "confidence": conf
                })

    if violations:
        print("\n🚨 SECURITY VIOLATION DETECTED 🚨")
        print(json.dumps(violations, indent=2))
        sys.exit(1)

    print("\n✅ No credentials detected")
    sys.exit(0)


if __name__ == "__main__":
    main()

