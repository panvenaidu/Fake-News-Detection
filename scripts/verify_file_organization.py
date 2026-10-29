"""Read-only checks for the UROP organization handoff; no training or network."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];J=R/'context/organization_20261029'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 moves=json.loads((J/'local_moves.json').read_text()); protected=json.loads((J/'protected_files.json').read_text())
 # .gitignore changed deliberately to protect newly organized private UI evidence.
 unchanged=[p for p,h in protected.items() if p!='.gitignore' and (R/p).exists() and sha(R/p)==h]
 assert len(unchanged)==len(protected)-1
 final=json.loads((J/'final_paths.json').read_text())
 for x in final:assert (R/x['path']).is_file() and sha(R/x['path'])==x['sha256'],x['path']
 for x in moves:assert not (R/x['old_path']).exists(),x['old_path']
 notebooks=list((R/'notebooks').rglob('*.ipynb'));assert len(notebooks)==11
 for p in notebooks:json.loads(p.read_text())
 cloud=json.loads((J/'kaggle_renames.json').read_text())['rows'];assert len(cloud)==11 and all(x['status']=='verified_renamed' and x['new_url'] for x in cloud)
 pages=[R/'START_HERE.md',R/'START_HERE.html',R/'FOLDER_GUIDE.md',R/'notebooks/README.md',R/'docs/README.md']+list((R/'docs/explainers').rglob('*.md'))+list((R/'docs/explainers').rglob('*.html'))
 checked=0
 for p in pages:
  for m in re.finditer(r'(?:\]\(|(?:href|src)=["\'])([^\s)"\']+)',p.read_text()):
   s=m[1].split('#')[0]
   if not s or re.match(r'^[a-z]+:|^/|^#',s):continue
   assert (p.parent/s).exists(),(str(p),s);checked+=1
 for p in (R/'docs/explainers').rglob('*.py'):compile(p.read_text(),str(p),'exec')
 print(json.dumps({'moves_verified':len(moves),'notebooks_byte_identity_and_json':len(notebooks),'protected_scientific_and_existing_files_unchanged':len(unchanged),'local_navigation_links_valid':checked,'kaggle_renames_from_durable_ui_receipt':len(cloud),'training_launched':False},indent=2))
if __name__=='__main__':main()
