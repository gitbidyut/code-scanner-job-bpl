import boto3
import json
import os
import sys

# ==========================
# Configuration
# ==========================
ENDPOINT_NAME = os.environ.get(
    "SAGEMAKER_ENDPOINT_NAME",
    "credential-scanner-endpoint"
)

# File types to scan
SCAN_EXTENSIONS = (
    ".py", ".js", ".ts", ".env", ".yaml", ".yml",
    ".json", ".tf", ".sh", ".txt"
)

# Max file size to scan (100 KB)
MAX_FILE_SIZE = 100 * 1024


# ==========================
# SageMaker runtime client
# ==========================
sm_runtime = boto3.client("sagemaker-runtime")


def invoke_model(text, file_path):
    """
    Invoke SageMaker endpoint for a single file
    """
    payload = {
        "text": text,
        "file": file_path
    }

    response = sm_runtime.invoke_endpoint(
        EndpointName="credential-scanner-endpoint",
        ContentType="application/json",
        Body=json.dumps(payload).encode("utf-8")
    )

    result = json.loads(response["Body"].read().decode("utf-8"))
    return result


def should_scan_file(path):
    """
    Decide whether a file should be scanned
    """
    if not path.endswith(SCAN_EXTENSIONS):
        return False

    if os.path.getsize(path) > MAX_FILE_SIZE:
        return False

    # Ignore git and terraform cache
    ignore_dirs = [".git", ".terraform", "node_modules", "__pycache__"]
    for d in ignore_dirs:
        if f"{os.sep}{d}{os.sep}" in path:
            return False

    return True


def scan_repository():
    """
    Walk through repository and scan files
    """
    findings = []

    for root, _, files in os.walk("."):
        for file in files:
            file_path = os.path.join(root, file)

            if not should_scan_file(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                print(f"⚠️  Could not read {file_path}: {e}")
                continue

            if not content.strip():
                continue

            result = invoke_model(content, file_path)

            if result.get("credential_found"):
                findings.append({
                    "file": file_path,
                    "type": result.get("type", "unknown"),
                    "confidence": result.get("confidence", "n/a")
                })

                print(f"❌ Credential detected in {file_path}")

    return findings


def main():
    print("🔍 Starting credential scan...")

    findings = scan_repository()

    if findings:
        print("\n🚨 SECURITY VIOLATION DETECTED 🚨")
        for f in findings:
            print(
                f"- File: {f['file']}, "
                f"Type: {f['type']}, "
                f"Confidence: {f['confidence']}"
            )

        # Fail the pipeline
        sys.exit(1)

    print("✅ Scan completed successfully. No credentials found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
