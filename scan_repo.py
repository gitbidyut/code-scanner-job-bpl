import os
import sys
import json
import boto3

ENDPOINT_NAME = "credential-scanner-endpoint"
REGION = "us-east-1"
THRESHOLD = 0.80

runtime = boto3.client("sagemaker-runtime", region_name=REGION)

print("🔍 Starting credential scan using SageMaker endpoint...")
print(f"📡 Endpoint: {ENDPOINT_NAME}")

def scan_file(filepath):
    # ✅ DEFINE content here
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/octet-stream",
        Accept="application/json",
        Body=content.encode("utf-8")   # ✅ content now exists
    )

    result = json.loads(response["Body"].read().decode("utf-8"))
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
                    violations.append(path)

    if violations:
        print("\n❌ Credential(s) detected:")
        for v in violations:
            print(v)
        sys.exit(1)

    print("\n✅ No credentials detected")
    sys.exit(0)

if __name__ == "__main__":
    main()