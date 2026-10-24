# Existing-credential probe only. Do not invoke sign-in or request new scopes.
from datetime import datetime,timezone
from pathlib import Path
import json, google.auth
probe={'utc':datetime.now(timezone.utc).isoformat(),'state':'existing_drive_api_credentials_probe','new_auth_invoked':False,'secrets_printed':False,'training':False}
try:
 credentials,project=google.auth.default()
 probe.update(credentials_available=True,credential_type=type(credentials).__module__+'.'+type(credentials).__name__)
 from google.auth.transport.requests import AuthorizedSession
 session=AuthorizedSession(credentials)
 response=session.get('https://www.googleapis.com/drive/v3/files/1i5d6pQvshJuQlwr1sQBskXClI0VtYXdX',params={'fields':'id,name,size,md5Checksum'},timeout=20)
 probe['http_status']=response.status_code
 if response.status_code==200: probe['receipt_metadata']=response.json()
 else: probe['error_reason']=response.json().get('error',{}).get('status','HTTP_ERROR')
 session.close()
except Exception as e: probe.update(credentials_available=False,error_type=type(e).__name__,error=str(e)[:400])
Path('/content/UROP_EXISTING_DRIVE_API_PROBE_20261025.json').write_text(json.dumps(probe,indent=2))
print(json.dumps(probe),flush=True)
