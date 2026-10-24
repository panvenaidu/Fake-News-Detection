"""Lossless transport grouping and restart checks; synthetic images only."""
import importlib.util,io,json,tarfile,tempfile,hashlib
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('pack',Path(__file__).resolve().parents[1]/'collab/repack_official_images_kaggle_v1.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def main():
    expected={str(i):{'id':str(i),'split':['train','validation','test'][i%3],'clean_title':'synthetic\nmultiline','6_way_label':i%6} for i in range(9)}
    with tempfile.TemporaryDirectory(dir='data/official_paired_v1',prefix='transport-check-') as tmp:
        source=Path(tmp)/'source';(source/'shards').mkdir(parents=True);original={}
        for group in range(3):
            archive=source/'shards'/f'original{group}.tar';rows=[]
            with tarfile.open(archive,'w') as tar:
                for i in range(group*3,group*3+3):
                    b=io.BytesIO();Image.new('RGB',(20,20),(i*20,1,2)).save(b,format='PNG');raw=b.getvalue();member=f'images/{i}.png';info=tarfile.TarInfo(member);info.size=len(raw);tar.addfile(info,io.BytesIO(raw));original[str(i)]=raw
                    rows.append({**expected[str(i)],'member':member,'bytes':len(raw),'image_sha256':hashlib.sha256(raw).hexdigest(),'source_member':f'author/{i}.png'})
            p.prep.record(archive.with_suffix('.receipt.json'),{'archive':archive.name,'bytes':archive.stat().st_size,'sha256':p.prep.sha(archive),'images':rows})
        output=source/'packed';first=p.pack(source,output,expected,target_bytes=3300,max_new_shards=1,check_scratch=False)
        assert not first['complete'] and first['images_committed']>0
        hashes={f.name:p.prep.sha(f) for f in (output/'shards').glob('*.tar')}
        (output/'shards/orphan.tar').write_bytes(b'untrusted')
        done=p.pack(source,output,expected,target_bytes=3300,check_scratch=False);assert done['complete'] and done['images_committed']==9 and not done['image_gate_passed']
        assert all(p.prep.sha(output/'shards'/n)==h for n,h in hashes.items())
        found={}
        for receipt in (output/'shards').glob('*.receipt.json'):
            d=json.loads(receipt.read_text())
            with tarfile.open(output/'shards'/d['archive']) as tar:
                for row in d['images']:
                    raw=tar.extractfile(row['member']).read();assert raw==original[row['id']] and row['source_member']==f"author/{row['id']}.png";assert all(row[k]==v for k,v in expected[row['id']].items());found[row['id']]=raw
        assert set(found)==set(expected)
        bad=next((output/'shards').glob('*.receipt.json'));d=json.loads(bad.read_text());(output/'shards'/d['archive']).write_bytes(b'corrupt')
        try:p.pack(source,output,expected,check_scratch=False)
        except ValueError:pass
        else:raise AssertionError('Corrupt packed generation accepted')
    result={'status':'passed','scope':'Synthetic9images only; full source CLI gate not bypassed','checks':['Bounded transport grouping and restart','Every image byte, ID, split, title, label and source path preserved','Previously committed packs unchanged','Orphan ignored','Corrupt committed pack rejected','Transport packing never marks runtime image gate passed'],'source_sha256':hashlib.sha256(Path(p.__file__).read_bytes()).hexdigest()}
    Path('results/multimodal_transport_repack_checks_20261024.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
