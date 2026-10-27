"""Independent saved CUDA/timing receipt verification; no model execution."""
import argparse,datetime,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
paths=list(a.folder.rglob('GPU_PREFLIGHT_SUMMARY.json'));assert len(paths)==1
path=paths[0];s=json.loads(path.read_text());assert s['state']=='gpu_preflight_verified'
def remap(old):return path.parent/Path(old).relative_to('/kaggle/working/urop_mm_part1_20261026')
fixture,measured=remap(s['fixture']),remap(s['throughput']);assert sha(fixture)==s['fixture_sha256'] and sha(measured)==s['throughput_sha256']
f=json.loads(fixture.read_text());m=json.loads(measured.read_text())
assert f['status']=='passed_cuda_engineering_fixture' and m['status']=='passed_measured_multimodal_preflight'
assert f['trainer_sha256']==m['trainer_sha256']=='7f7fb90deb08a5901d1ca8343b780f6d82dd42b3e278d51f333568435becee0e'
assert f['recovery_sha256']==m['recovery_sha256']=='2f5f67ce79289c69279040d21b483e28535895f5c99c63e0021da3eee6d3d1c8'
assert m['config_sha256']=='ad8f86f86b1fef453ae3bccda0aeb13cc50b298dc0d5d502f87c9ac4b041b483'
assert m['train_only'] and m['measurement_seconds']>=600 and m['test_performed'] is False and m['scientific_epochs_completed']==0 and m['full_validations_completed']==0
assert m['inputs']['split_counts']=={'train':563601,'validation':59299,'test':59270}
assert s['coverage_sha256']=='afe8c723f91fe74f791908e0c16fab94d919af64c7cb7c9b5a37e676361d95e5' and s['packed_index_sha256']=='fc8dc03a4f773da5762891c8392375add5fb8087251b527f3b37a880308e6018'
assert f['torch']==m['torch'] and f['cuda']==m['cuda'] and f['device']==m['device']
train,evaluate,save=m['train_examples_per_second'],m['eval_path_examples_per_second'],m['checkpoint_seconds']
assert all(math.isfinite(x) for x in [train,evaluate,save]) and min(train,evaluate)>0 and save>=0
epoch=563601/train+59299/evaluate+save;assert math.isclose(epoch,s['estimated_epoch_seconds'],rel_tol=1e-10)
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_saved_preflight_readback','summary_sha256':sha(path),'fixture_sha256':sha(fixture),'measured_sha256':sha(measured),'train_samples_per_second':train,'eval_path_samples_per_second':evaluate,'loader_wait_fraction':m['train_loader_wait_seconds']/m['measurement_seconds'],'estimated_epoch_hours':epoch/3600,'estimated_two_epochs_hours':2*epoch/3600,'full_epoch_fits_12h_with_margin':1.25*epoch+600+3600<43200,'gpu':m['device'],'versions':m['versions'],'runtime_reader_sha256':s.get('runtime_reader_sha256'),'scientific_training':False,'test_performed':False}
a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
