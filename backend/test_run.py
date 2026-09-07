import requests
import time
import json

url = 'http://127.0.0.1:8000/api/analyses'
pdf_path = 'backend/storage/uploads/CP100P.pdf'
txt_path = 'backend/storage/uploads/CP100P.txt'

with open(pdf_path, 'rb') as f_pdf, open(txt_path, 'rb') as f_txt:
    files = {
        'pdf_file': ('CP100P.pdf', f_pdf, 'application/pdf'),
        'config_file': ('CP100P.txt', f_txt, 'text/plain')
    }
    data = {
        'project_name': 'CP100P AI Master Logic Analysis',
        'pdf_revision': 'Rev-1',
        'config_revision': 'Rev-1'
    }
    r = requests.post(url, files=files, data=data)
    print('POST response:', r.status_code)
    res_json = r.json()
    job_id = res_json.get('job_id') or res_json.get('id')
    print('Job ID:', job_id)

for attempt in range(60):
    time.sleep(2)
    res = requests.get(f'{url}/{job_id}').json()
    status = res.get('status')
    print(f'Attempt {attempt+1}: Status = {status}')
    if status == 'COMPLETED':
        devs = res.get('deviations', [])
        print(f'SUCCESS! Completed with {len(devs)} deviations.')
        for d in devs:
            page = d.get('page_number')
            block = d.get('block_name')
            exp = d.get('explanation')
            print(f'Page {page:2d} | Block: {block:20s} | Deviation: {exp}')
        break
    elif status == 'FAILED':
        print('FAILED:', res.get('error_message'))
        break
