import json

JSON_FILE_NAME = "insiightprep-firebase-adminsdk-fbsvc-4ef5cd9455.json"

with open(JSON_FILE_NAME, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"FIREBASE_SERVICE_ACCOUNT_JSON='{json.dumps(data, separators=(',', ':'))}'")
