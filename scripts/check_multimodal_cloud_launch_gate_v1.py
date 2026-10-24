"""Launch contract rejection checks. Mock receipts only; no GPUs/network/model."""
import copy,datetime,hashlib,importlib.util,json,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('launch',Path(__file__).resolve().parents[1]/'collab/kaggle_multimodal_part1_cell_v1.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def main():
    with tempfile.TemporaryDirectory(dir='data/official_paired_v1',prefix='launch-gate-check-') as temp:
        root=Path(temp);work=root/'working';work.mkdir()
        def ref(name,data):
            path=root/name;path.write_text(json.dumps(data));return {'path':str(path),'sha256':p.sha(path)}
        # Deliberately synthetic metadata; no dataset validity claim is produced.
        coverage=ref('mock_coverage.json',{'image_gate_passed':True,'required':682661,'usable':682661,'split_counts':p.COUNTS})
        fixture=ref('mock_cuda.json',{'status':'passed_cuda_engineering_fixture','trainer_sha256':p.SOURCE_HASHES['scripts/train_official_multimodal_v1.py'],'recovery_sha256':p.SOURCE_HASHES['scripts/multimodal_recovery_v1.py']})
        timing=ref('mock_timing.json',{'status':'passed_measured_multimodal_preflight','train_only':True,'measurement_seconds':600,'trainer_sha256':p.SOURCE_HASHES['scripts/train_official_multimodal_v1.py'],'config_sha256':p.SOURCE_HASHES['configs/multimodal_official_6way_v1.json'],'train_examples_per_second':100,'eval_path_examples_per_second':200,'checkpoint_seconds':60})
        release={'state':'registered_after_verified_full_preflight','stage':'part1','stop_after_epoch':1,'final_test':False,'source_commit':p.SOURCE_COMMIT,'resume':False,'input_root':'/kaggle/input/datasets/rocky62/mock-not-real','output':str(work/'attempt'),'conflicting_attempt_jobs':[],'active_job_check_utc':p.now(),'private_input_version':1,'coverage':coverage,'cuda_fixture':fixture,'throughput':timing,'wall_seconds':10000,'verified_session_seconds_remaining':14000}
        p.check_release(release,work)
        cases=[('draft',{'state':'DRAFT_NOT_LAUNCHABLE'}),('test',{'final_test':True}),('epoch3',{'stop_after_epoch':3}),('part2',{'stage':'part2'}),('existing_job',{'conflicting_attempt_jobs':['other']}),('stale_check',{'active_job_check_utc':(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=11)).isoformat()}),('escape',{'output':str(root/'outside')}),('working_input',{'input_root':str(work/'images')}),('no_save_margin',{'wall_seconds':13000}),('too_short_epoch',{'wall_seconds':100}),('invalid_version',{'private_input_version':True}),('unverified_resume',{'resume':True})]
        for label,changes in cases:
            altered={**release,**changes}
            try:p.check_release(altered,work)
            except (ValueError,KeyError,TypeError):pass
            else:raise AssertionError('Unsafe release accepted: '+label)
        altered=copy.deepcopy(release);altered['coverage']['sha256']='0'*64
        try:p.check_release(altered,work)
        except ValueError:pass
        else:raise AssertionError('Tampered evidence accepted')
        altered=copy.deepcopy(release);altered['coverage']=ref('mock_incomplete.json',{'image_gate_passed':False,'required':682661,'usable':505573,'split_counts':p.COUNTS})
        try:p.check_release(altered,work)
        except ValueError:pass
        else:raise AssertionError('Incomplete data accepted')
    result={'status':'passed','scope':'Mock metadata release-gate rejection checks only; no real data/CUDA/throughput/model execution','checks':['Reject draft, test inference, Part2 and epoch3','Reject conflicting/stale job evidence','Reject input/output path escapes and invalid input version','Reject missing save margin or insufficient measured epoch budget','Reject unverified resume and tampered/incomplete evidence'],'source_sha256':hashlib.sha256(Path(p.__file__).read_bytes()).hexdigest(),'actual_cloud_launch_tested':False}
    Path('results/multimodal_cloud_launch_gate_checks_20261024.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
