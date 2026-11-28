
from qa_common import *
import hashlib
tables=["clinics","users","dentists","patients","medical_records","appointments","clinical_access_links","clinical_access_events","clinical_evolutions","audit_logs"]
result={}
for table in tables:
 rows=q("SELECT * FROM "+table+" ORDER BY id")
 result[table]={"count":len(rows),"sha256":hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()}
print(json.dumps(result,sort_keys=True))
