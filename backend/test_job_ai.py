import time
import os
from backend.app.core.job_runner import job_runner
from backend.app.schemas.types import JobStatus

pdf = r"C:\Users\karsa\Downloads\dktp pdf files\CP100P.pdf"
txt = r"C:\Users\karsa\Downloads\dktp text files\CP100P.txt"

jid = job_runner.create_analysis_job(pdf, txt, project_name="Pure AI Test")
print("Created job:", jid)

for _ in range(40):
    time.sleep(1)
    a = job_runner.get_analysis(jid)
    print(f"Status: {a.status}, Deviations: {len(a.deviations)}")
    if a.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
        break

print(f"\nFinal Deviations Count: {len(a.deviations)}")
for d in a.deviations[:5]:
    print(f"Line {d.config_evidence.line_start}: [{d.type}] {d.block_name} -> {d.explanation}")
