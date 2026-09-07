import time
import requests

url = "http://127.0.0.1:8000/api/analyses"
files = {
    "pdf_file": open(r"C:\Users\karsa\Downloads\dktp pdf files\CP100P.pdf", "rb"),
    "config_file": open(r"C:\Users\karsa\Downloads\dktp text files\CP100P.txt", "rb")
}
data = {"project_name": "Pure AI Live Test"}

r = requests.post(url, files=files, data=data)
print("Submit response:", r.status_code, r.json())
jid = r.json()["job_id"]

for i in range(25):
    time.sleep(1)
    res = requests.get(f"http://127.0.0.1:8000/api/analyses/{jid}").json()
    status = res.get("status")
    dev_count = len(res.get("deviations", []))
    print(f"[{i+1}s] Status: {status}, Deviations: {dev_count}")
    if status in ["COMPLETED", "FAILED"]:
        break

print("\n--- PURE AI DEVIATIONS RESULT ---")
print("Total Deviations:", len(res.get("deviations", [])))
for d in res.get("deviations", []):
    ln = d.get("config_evidence", {}).get("line_start")
    print(f"Line {ln}: [{d.get('type')}] {d.get('block_name')} -> {d.get('explanation')}")
