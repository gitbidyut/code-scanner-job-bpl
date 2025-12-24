import os
import sys
import json
import boto3

ENDPOINT_NAME = "credential-scanner-endpoint"
THRESHOLD = 0.80
REGION = "us-east-1"

runtime = boto3.client("sagemaker-runtime", region_name=REGION)

print("🔍 Starting credential scan using SageMaker endpoint...")
print(f"📡 Endpoint: {ENDPOINT_NAME}")

def scan_file(filepath):
    with open(filepath, "r", errors="ignore") as f:
        content = f.read()

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="text/plain",
        Body=content.encode("utf-8")
    )

    result = json.loads(response["Body"].read().decode())
    return result["prediction"], result["confidence"]

def main():
    violations = []

    for root, _, files in os.walk(os.getcwd()):
        for name in files:
            if name.endswith((".py", ".tf", ".yml", ".yaml", ".txt", ".json")):
                path = os.path.join(root, name)

                pred, conf = scan_file(path)
                print(f"➡️ {path} | confidence={conf:.3f}")

                if pred == 1 and conf >= THRESHOLD:
                    violations.append({
                        "file": path,
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
