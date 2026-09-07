import os
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

pdf_dir = r"C:\Users\karsa\Downloads\dktp pdf files"
pdf1 = os.path.join(pdf_dir, "CP000A.pdf")
pdf2 = os.path.join(pdf_dir, "CP000B.pdf")

print("Uploading 2 PDFs for Deviation Comparison...")
t0 = time.time()

with open(pdf1, 'rb') as f1, open(pdf2, 'rb') as f2:
    files = {
        'pdf_file': ('Drawing_RevA.pdf', f1, 'application/pdf'),
        'config_file': ('Drawing_RevB.pdf', f2, 'application/pdf'),
    }
    data = {'project_name': 'Drawing Revision Comparison (Rev A vs Rev B)'}
    res = requests.post(f"{BASE_URL}/api/analyses", files=files, data=data)

print("Response:", res.status_code, res.json())
job_id = res.json()["job_id"]

for i in range(45):
    time.sleep(1)
    status_res = requests.get(f"{BASE_URL}/api/analyses/{job_id}")
    d = status_res.json()
    status = d.get("status")
    print(f"[{i+1}s] Status: {status} | Deviations: {len(d.get('deviations', []))}")
    if status == "COMPLETED":
        print(f"\n--- PDF vs PDF SUCCESS in {time.time()-t0:.2f}s ---")
        print("Total Deviations:", d["stats"]["total_deviations"])
        print("Critical:", d["stats"]["critical_count"])
        print("High:", d["stats"]["high_count"])
        print("Medium:", d["stats"]["medium_count"])
        for dev in d["deviations"][:8]:
            print(f"  * [{dev['deviation_number']}] {dev['type']} ({dev['severity']}) - Drawing 1: '{dev['pdf_expected']}' vs Drawing 2: '{dev['config_actual']}'")
        break
    elif status == "FAILED":
        print("Failed:", d.get("error_message"))
        break
