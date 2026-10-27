"""Bounded official-API Part1 continuation: verify, epoch1, verify, epoch2.

Receives the already-approved credential in RAM through a FIFO. Never trains on
the laptop, changes protocol, tests, retries an ambiguous submission or launches
beyond epoch2. STOP_PIPELINE prevents the next launch without killing a job.
"""
import argparse, datetime, hashlib, json, os, shutil, stat, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'data/cloud_recovery/part1_verified_pipeline_20261027'
RESULTS = ROOT/'results'
PREF = ROOT/'data/cloud_recovery/KAGGLE_RAW_CACHE_PREFLIGHT_v1_20261027'
PREF_KERNEL = 'rocky62/urop-mm-raw-cache-preflight-20261027/1'
SLUG = 'rocky62/urop-mm-part1-science-usable-20261027'
ATTEMPT = 'OFFICIAL-6W-MM-USABLE-v2_seed42_20261027'
DOCS = ['context/RESUME_HERE.md','context/PROJECT_CONTEXT.md','context/DECISIONS.md',
        'context/EXPERIMENT_LOG.md','context/TASK_REPORT.md','collab/COLAB_WORKLOG.md',
        'work_logs/MODEL_STATUS.md','README.md','context/MM_PART1_CURRENT_STATE_20261027.md']

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    with temporary.open('w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temporary,path)
def command(args):
    return subprocess.run([str(x) for x in args],cwd=ROOT,check=True,capture_output=True,text=True)
def journal(state,**kw):
    value={'utc':utc(),'state':state,**kw};write(BASE/'status.json',value)
    print(json.dumps(value),flush=True)
def stopped():
    if (BASE/'STOP_PIPELINE').exists():raise RuntimeError('STOP_PIPELINE: preserve current durable handoff; no next job launched')
def checkpoint(title,epochs,receipt,extra=''):
    report=ROOT/'context/MM_PART1_PIPELINE_CURRENT_20261027.md'
    report.write_text('# Verified Part1 pipeline checkpoint\n\n'+utc()+' — '+title+'\n\n'+
        f'Completed full scientific training {epochs}/2; full validation {epochs}/2. '
        'No final test. This is one four-epoch experiment, stopped after epoch2.\n\n'+
        f'Evidence: `{receipt.relative_to(ROOT)}`. '+extra+'\n\n'+
        'Bounded controller: `collab/run_verified_part1_pipeline_v1.py`; live journal '
        '`data/cloud_recovery/part1_verified_pipeline_20261027/status.json`. '
        'A STOP_PIPELINE file in that folder prevents the next job. Verify saved launch receipts '
        'before recovery; never duplicate a submitted notebook.\n')
    header='<!-- PART1_PIPELINE_CURRENT -->\nLatest verified checkpoint: `context/MM_PART1_PIPELINE_CURRENT_20261027.md`.\n<!-- /PART1_PIPELINE_CURRENT -->\n\n'
    for name in DOCS:
        path=ROOT/name;s=path.read_text()
        if '<!-- PART1_PIPELINE_CURRENT -->' not in s:path.write_text(header+s)
    tracker=RESULTS/'PROGRESS_TRACKER.json';p=json.loads(tracker.read_text());p['updated_utc']=utc()
    m=p['models']['text_plus_image'];m.update(epochs_trained=epochs,epochs_validated=epochs,
        state=title,checkpoint_completion_percent=40+10*epochs)
    m['milestones'].update(training=epochs/4,validation=epochs/4)
    m['data_preparation'].update(image_runtime_gate_passed=True,packed_reader_production_integration_complete=True,
        training_epochs_completed=epochs,full_validations_completed=epochs)
    p['overall_three_modality_checkpoint_percent']=round((100+40+10*epochs+20)/3)
    p['current_verified_part1_receipt']=str(receipt.relative_to(ROOT));write(tracker,p)
    md=RESULTS/'PROGRESS_TRACKER.md'
    md.write_text('# UROP verified workflow progress\n\n'+utc()+'\n\n'+
        f'Text-only: 100%. Text + image: {40+10*epochs}%. Image-only: 20%. '
        f'Overall: {p["overall_three_modality_checkpoint_percent"]}%.\n\n'+
        f'Full multimodal training {epochs}/4, validation {epochs}/4, final test 0. '
        f'Part1 requires two epochs and two validations. {title}.\n\n'+
        'Evidence: `'+str(receipt.relative_to(ROOT))+'`.\n')
    owned=[str(report.relative_to(ROOT)),*DOCS,'results/PROGRESS_TRACKER.json','results/PROGRESS_TRACKER.md',str(receipt.relative_to(ROOT))]
    command(['git','add','--',*owned]);staged=command(['git','diff','--cached','--name-only']).stdout.splitlines()
    assert set(staged).issubset(set(owned)),'Unrelated staged files: stop before commit'
    if staged:command(['git','commit','-m',title])
    command(['git','push','origin','main']);head=command(['git','rev-parse','HEAD']).stdout.strip()
    remote=command(['git','ls-remote','origin','refs/heads/main']).stdout.split()[0];assert head==remote
    write(RESULTS/('MM_PART1_PIPELINE_GIT_EPOCH%d_20261027.json'%epochs),{'utc':utc(),'local_commit':head,'remote_commit':remote,'verified':True})

def run(api):
    deadline=time.monotonic()+30*3600
    def retry(fn):
        for n in range(3):
            try:return fn()
            except Exception as e:
                response=getattr(e,'response',None)
                if n==2 or response is None or response.status_code not in [429,500,502,503,504]:raise
                time.sleep(2**n)
    def wait(kernel,cap):
        end=min(deadline,time.monotonic()+cap);previous=None
        while time.monotonic()<end:
            status=retry(lambda:api.kernels_status(kernel));state=str(status.status)
            write(BASE/'live_cloud_status.json',{'utc':utc(),'kernel':kernel,'status':state,'failure_message':status.failure_message})
            if state!=previous:journal('cloud_job_observed',kernel=kernel,status=state);previous=state
            if state not in ['KernelWorkerStatus.RUNNING','KernelWorkerStatus.QUEUED']:
                assert state=='KernelWorkerStatus.COMPLETE',f'{kernel}: {state}: {status.failure_message}'
                return
            time.sleep(60)
        raise TimeoutError('Bounded cloud wait expired; preserve submitted job')
    def inspect(kernels,path):
        q=retry(api.quota_view);g=q.gpu_quota
        value={'utc':utc(),'request_succeeded':True,'gpu_quota':{k:getattr(g,k).total_seconds() for k in ['time_used','time_reserved','total_time_allowed']},
               'kernels':{k:str(retry(lambda:api.kernels_status(k)).status) for k in kernels}}
        write(path,value);return value
    def output(kernel,folder,pattern):
        files,page=retry(lambda:api.kernels_output(kernel,str(folder),file_pattern=pattern,force=False,quiet=True,page_size=100))
        assert not page,'Unexpected output pagination: retain and inspect before continuation'
        return files
    journal('waiting_verified_raw_cache_preflight',kernel=PREF_KERNEL)
    wait(PREF_KERNEL,7500)
    # The existing read-only watcher owns this first download. Reuse its files.
    watcher=RESULTS/'MM_PART1_WATCH_RAW_CACHE_PREFLIGHT_20261027.json'
    for _ in range(180):
        if watcher.exists() and json.loads(watcher.read_text()).get('request_succeeded'):break
        time.sleep(2)
    else:raise RuntimeError('Preflight readback watcher not complete; do not duplicate download')
    pref_receipt=RESULTS/'MM_PART1_RAW_CACHE_PREFLIGHT_VERIFIED_20261027.json'
    command([sys.executable,ROOT/'scripts/verify_saved_mm_preflight_v1.py','--folder',PREF,'--output',pref_receipt])
    verified=json.loads(pref_receipt.read_text());assert verified['full_epoch_fits_12h_with_margin']
    summary=next(PREF.rglob('GPU_PREFLIGHT_SUMMARY.json'));s=json.loads(summary.read_text())
    assert s['runtime_reader_sha256']==sha(ROOT/'scripts/packed_image_io_v3.py')
    checkpoint('Verified cloud scratch throughput; scientific training not started',0,pref_receipt)
    prior_folder=None;prior_version=None
    for epoch in [1,2]:
        stopped()
        launch_file=BASE/('epoch%d_launch.json'%epoch)
        package=BASE/('epoch%d_package'%epoch)
        if launch_file.exists():
            launch=json.loads(launch_file.read_text());assert launch.get('submitted') and launch.get('version')
        else:
            audit_file=BASE/('epoch%d_api_check.json'%epoch)
            kernels=[PREF_KERNEL,'rocky62/urop-mm-packed-faculty-image-gate-20261026/2']
            if epoch==2:kernels.append(SLUG+'/'+str(prior_version))
            audit=inspect(kernels,audit_file);assert all(x=='KernelWorkerStatus.COMPLETE' for x in audit['kernels'].values())
            q=audit['gpu_quota'];available=q['total_time_allowed']-q['time_used']-q['time_reserved']
            required=(3-epoch)*(1.25*(s['estimated_epoch_seconds']+s['raw_archive_cache']['seconds'])+600)+3600
            assert available>required,'Insufficient GPU quota for remaining registered epochs with reserve'
            assert shutil.disk_usage(ROOT).free>16*1024**3,'Insufficient laptop artifact backup space'
            args=[sys.executable,ROOT/'collab/build_kaggle_science_job_v1.py','--preflight',PREF,'--preflight-kernel',PREF_KERNEL,
                  '--metadata',PREF/'notebook_metadata/kernel-metadata.json','--api-check',audit_file,'--destination',package,'--epoch',epoch]
            if epoch==2:args+=['--previous',prior_folder,'--previous-version',prior_version]
            command(args);stopped()
            audit=json.loads((package/'launch_audit.json').read_text());cap=audit['session_timeout_seconds']
            write(launch_file,{'utc':utc(),'submitted':False,'mutation_pending':True,'package':str(package),'package_sha256':sha(package/'registered_epoch.ipynb')})
            # Exactly one mutation attempt. Ambiguous network failure requires inspection.
            r=api.kernels_push(str(package),timeout=str(cap),acc='NvidiaTeslaT4',no_run=False)
            assert not r.error and not r.invalid_kernel_sources and not r.invalid_dataset_sources
            launch={'utc':utc(),'submitted':True,'version':r.version_number,'kernel_id':r.kernel_id,'url':r.url,'session_timeout_seconds':cap,'package_sha256':sha(package/'registered_epoch.ipynb')}
            write(launch_file,launch)
        kernel=SLUG+'/'+str(launch['version'])
        journal('scientific_epoch_submitted',epoch=epoch,kernel=kernel,launch=launch)
        wait(kernel,launch['session_timeout_seconds']+600)
        folder=BASE/('epoch%d_saved_output'%epoch)
        files=output(kernel,folder,ATTEMPT+r'/|registered_job_release\.json|_console\.log$')
        attempt=folder/'urop_mm_science_20261027'/ATTEMPT;assert attempt.is_dir()
        receipt=RESULTS/('MM_PART1_EPOCH%d_VERIFIED_20261027.json'%epoch)
        command([ROOT/'.venv-urop/bin/python',ROOT/'scripts/verify_saved_mm_epoch_v1.py','--project',ROOT,'--run',attempt,'--epochs',epoch,'--output',receipt])
        proof=json.loads(receipt.read_text());assert proof['epochs_trained']==epoch and proof['epochs_validated']==epoch and proof['no_test_performed']
        proof['private_cloud_saved_version']={'kernel':kernel,'url':launch['url'],'kernel_id':launch['kernel_id'],'retrieved_files':len(files),'independent_readback':True}
        write(receipt,proof)
        checkpoint('Verified Part1 epoch%d training validation and recovery'%epoch,epoch,receipt,
                   'Private immutable output: '+kernel+'. Recovery next epoch '+str(epoch+1)+', cursor0. No final test.')
        prior_folder,prior_version=folder,launch['version']
        journal('epoch_fully_verified_and_backed_up',epoch=epoch,kernel=kernel,receipt=str(receipt))
    journal('part1_scientific_acceptance_verified',epochs_trained=2,epochs_validated=2,no_test_performed=True,
            next='Assistant reviews final reports, receipts and remote Git before marking Goal complete; Part2 remains unstarted')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--token-fifo',type=Path,required=True);a=p.parse_args()
    BASE.mkdir(parents=True,exist_ok=True)
    lock=BASE/'controller.lock'
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        assert a.token_fifo.resolve().is_relative_to(ROOT) and stat.S_ISFIFO(a.token_fifo.stat().st_mode)
        with a.token_fifo.open() as f:token=f.read().strip()
        a.token_fifo.unlink();assert token.startswith('KGAT_')
        os.environ['KAGGLE_API_TOKEN']=token;os.environ['KAGGLE_CONFIG_DIR']=str(ROOT/'data/cloud_recovery/.kaggle-api-config')
        from kaggle.api.kaggle_api_extended import KaggleApi
        api=KaggleApi();api.authenticate();run(api)
    except Exception as error:
        # Exception messages can contain provider details; record only safe type.
        journal('pipeline_stopped_preserve_artifacts',error_type=type(error).__name__,next='Inspect saved job/output and failing guard; never blindly resubmit')
        raise
    finally:lock.unlink(missing_ok=True)
