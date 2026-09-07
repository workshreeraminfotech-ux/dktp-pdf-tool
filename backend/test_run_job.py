import requests
import time

BASE_URL = "http://127.0.0.1:8000"

print("Triggering Demo Analysis...")
t0 = time.time()
res = requests.post(f"{BASE_URL}/api/analyses/demo")
print("Response:", res.status_code, res.json())
job_id = res.json()["job_id"]

for i in range(30):
    time.sleep(1)
    status_res = requests.get(f"{BASE_URL}/api/analyses/{job_id}")
    data = status_res.json()
    status = data.get("status")
    print(f"[{i+1}s] Status: {status} | Deviations: {len(data.get('deviations', []))}")
    if status == "COMPLETED":
        print(f"\n--- SUCCESS in {time.time()-t0:.2f}s ---")
        print("Total Deviations:", data["stats"]["total_deviations"])
        print("Critical:", data["stats"]["critical_count"])
        print("High:", data["stats"]["high_count"])
        print("Medium:", data["stats"]["medium_count"])
        for dev in data["deviations"][:5]:
            print(f"  * [{dev['deviation_number']}] {dev['type']} ({dev['severity']}) - PDF: {dev['pdf_expected']} vs CFG: {dev['config_actual']}")
        break
    elif status == "FAILED":
        print("Job failed:", data.get("error_message"))
        break
