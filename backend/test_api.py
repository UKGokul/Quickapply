import urllib.request
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyOWNmM2EyMC04Njg4LTQzMWEtYjVmMC0yYTVhNDNhMjA5NzYiLCJleHAiOjE3NzczODQyOTR9.yqD-5vNldILJ8MwhJg85jq_ZTlG3EUOliHaAdhbHoNw"

def request(method, url, data=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:8000{url}",
        data=json.dumps(data).encode("utf-8") if data else None,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        },
        method=method
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def post(url, data):
    return request("POST", url, data)

def get(url):
    req = urllib.request.Request(
        f"http://127.0.0.1:8000{url}",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def patch(url, data):
    return request("PATCH", url, data)

# Create application
print("=== CREATING APPLICATION ===")
result = post("/applications/", {
    "type": "job",
    "position_title": "Python Backend Developer",
    "organization": "Tech Company GmbH",
    "location": "Hamburg, Germany",
    "deadline": "2026-05-01",
    "contact_email": "hr@techcompany.de",
    "notes": "Found on LinkedIn"
})
print(result)
app_id = result["application_id"]

# List applications
print("\n=== ALL APPLICATIONS ===")
print(get("/applications/"))

# Update status
print("\n=== UPDATING STATUS ===")
result = patch(f"/applications/{app_id}/status", {"status": "applied"})
print(result)