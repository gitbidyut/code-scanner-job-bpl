import os
import sys
import json
import re
import boto3

# -----------------------------
# Configuration
# -----------------------------
ENDPOINT_NAME = os.environ.get(
    "SAGEMAKER_ENDPOINT_NAME",
    "credential-scanner-endpoint"
)

CONFIDENCE_THRESHOLD = 0.85

IGNORED_EXTENSIONS = {
    ".tf",
    ".tfvars",
    ".yml",
    ".yaml",
    ".json",
    ".md",
    ".txt",
    ".ini",
    ".cfg",
    ".requirements"
}

MAX_FILE_SIZE = 200_000  # 200 KB safety limit

# Real credential patterns (cheap & precise)
SUSPICIOUS_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",                      # AWS access key
    r"ASIA[0-9A-Z]{16}",                      # AWS STS key
    r"(?i)aws_secret_access_key\s*=\s*['\"][^'\"]+['\"]",
    r"(?i)aws_access_key_id\s*=\s*['\"][^'\"]+['\"]",
    r"(?i)secret[_\- ]?key\s*=\s*['\"][^'\"]+['\"]",
    r"(?i)password\s*=\s*['\"][^'\"]+['\"]",
]


# -----------------------------
# Helpers
# -----------------------------
def looks_like_real_secret(text: str) -> bool:
    return any(re.search(p, text) for p in SUSPICIOUS_PATTERNS)


def should_skip_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in IGNORED_EXTENSIONS


def invoke_endpoint(client, text: str) -> dict:
    response = client.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps({"text": text}),
    )
    return json.loads(response["Body"].read())


# -----------------------------
# Main scan logic
# -----------------------------
def main():
    print("Starting credential scan...")

    sm_runtime = boto3.client("sagemaker-runtime")
    violations = []

    for root, _, files in os.walk("."):
        for name in files:
            path = os.path.join(root, name)

            # if should_skip_file(path):
            #     print(f"Skipping {path} (safe extension)")
            #     continue

            try:
                if os.path.getsize(path) > MAX_FILE_SIZE:
                    print(f"ℹ️ Skipping {path} (file too large)")
                    continue

                with open(path, "r", errors="ignore") as f:
                    content = f.read()

            except Exception as e:
                print(f"⚠️ Could not read {path}: {e}")
                continue

            # Cheap regex gate
            if not looks_like_real_secret(content):
                continue

            # Call ML model only when needed
            result = invoke_endpoint(sm_runtime, content)

            if (
                result.get("credential_found")
                and result.get("confidence", 0) >= CONFIDENCE_THRESHOLD
            ):
                print(f"❌ Credential detected in {path}")
                violations.append({
                    "file": path,
                    "type": result.get("type", "unknown"),
                    "confidence": result.get("confidence"),
                })

    if violations:
        print("\n🚨 SECURITY VIOLATION DETECTED 🚨")
        for v in violations:
            print(
                f"- File: {v['file']}, "
                f"Type: {v['type']}, "
                f"Confidence: {v['confidence']}"
            )
