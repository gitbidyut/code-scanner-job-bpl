import os
import sys
import json
import joblib

MODEL_DIR = "/opt/ml/model" if os.path.exists("/opt/ml/model") else "./model"
REPO_DIR = os.getcwd()   # CodeBuild working directory
THRESHOLD = 0.80

print("🔍 Starting credential scan...")
print(f"📂 Scanning directory: {REPO_DIR}")

def load_model():
    print("📦 Loading model...")
    vectorizer = joblib.load(os.path.join(MODEL_DIR, "vectorizer.joblib"))
    model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    return vectorizer, model

def scan_file(filepath, vectorizer, model):
    with open(filepath, "r", errors="ignore") as f:
        content = f.read()

    X = vectorizer.transform([content])
    prob = model.predict_proba(X)[0][1]
    pred = int(prob >= THRESHOLD)

    return pred, prob

def main():
    vectorizer, model = load_model()

    findings = []

    for root, _, files in os.walk(REPO_DIR):
        for name in files:
            if name.endswith((".py", ".tf", ".yml", ".yaml", ".txt", ".json")):
                path = os.path.join(root, name)
                pred, prob = scan_file(path, vectorizer, model)

                print(f"➡️ {path} | confidence={prob:.3f}")

                if pred == 1:
                    findings.append({
                        "file": path,
                        "confidence": prob
                    })

    if findings:
        print("\n🚨 SECURITY VIOLATION DETECTED 🚨")
        print(json.dumps(findings, indent=2))
        sys.exit(1)

    print("\n✅ No credentials detected")
    sys.exit(0)

if __name__ == "__main__":
    main()
