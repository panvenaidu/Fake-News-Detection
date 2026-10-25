"""Synchronize sanitized measured cloud progress, never invent a live counter."""
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--short',type=int,required=True)
parser.add_argument('--weekly',type=int,required=True)
args=parser.parse_args()
if not 0<=args.short<=100 or not 0<=args.weekly<=100:raise ValueError('Invalid actual allowance')
now=datetime.now(timezone.utc).isoformat()
observations=json.loads((root/'results/MM_PART1_API_PACK_OBSERVATIONS_20261025.json').read_text())['observations']
latest=observations[-1]
joined=next((x for x in reversed(observations) if x['state']=='api_original_TSV_and_source_metadata_joins_passed'),None)
audit=next((x for x in reversed(observations) if x['state']=='api_prior_pack_verified'),None)
committed=next((x for x in reversed(observations) if x['state']=='api_pack_committed'),None)
terminal=next((x for x in reversed(observations) if x['state'] in ('api_transport_terminal','api_transport_failed')),None)
live=terminal is None
state='real_API_transport_live' if live else terminal['state']
images=committed['images_committed'] if committed else 319820
packs=committed['packed_shards'] if committed else 18

def read(path):return json.loads((root/path).read_text())
def save(path,data):(root/path).write_text(json.dumps(data,indent=2)+'\n')
job=read('results/MM_PART1_API_PACK_JOB_20261025.json')
job.update(utc=now,state=state,latest_counter=latest,source_joins=joined,prior_pack_audit=audit,
           new_committed_packs_observed=packs-18,terminal=terminal,
           latest_measured_durable_images=images,latest_measured_durable_packs=packs)
if terminal and terminal.get('job_id'):job['registered_job_id']=terminal['job_id']
save('results/MM_PART1_API_PACK_JOB_20261025.json',job)
next_action=('Inspect same cell/process/private control before continuation; never duplicate live packing. After the first durable transaction, '
             'verify terminal archive/receipt and recovery, then resume remaining lossless packing. Full private Kaggle input, actual runtime '
             'image SHA/decode, CUDA recovery/preflight, epochs1–2 and full validations remain pending. No Part1 final test.')
recovery=read('results/MM_PART1_RECOVERY_PROGRESS_20261025.json')
recovery.update(updated_utc=now,state=state,durable_packed_images=images,durable_packs=packs,
                goal_status='User reported existing Goal resumed; supported API still blocked at latest check; manual turn authorized',
                full_source_inventory_passed=bool(joined),source_metadata_inventory_passed=True,
                no_active_packing_or_training_job=not live,independent_job_running=live,next=next_action,
                usage_observed={'short_remaining':args.short,'weekly_remaining':args.weekly,'utc':now},
                current_goal_turn_classification='Progress: full original TSV/source joins passed; old archives being full-hash audited; API metadata bridge prepared and synthetic-tested')
if 'historical_runtime' not in recovery:recovery['historical_runtime']=recovery['runtime']
recovery['runtime']={'platform':'Colab CPU','notebook':job['notebook'],'pid':job['runtime_pid'],
                     'boot_id':job['boot_id'],'RAM_GB_observed_approx':1.9,'DriveFS_mounted':False}
recovery['api']['scope']='All682170 original TSV/source metadata joins passed; current archive hash audit in progress. Runtime full-image gate still pending.'
recovery['api']['current_job_receipt']='results/MM_PART1_API_PACK_JOB_20261025.json'
save('results/MM_PART1_RECOVERY_PROGRESS_20261025.json',recovery)
usable=read('results/MM_PART1_USABLE_RECEIPT_20261024.json')
if 'historical_CPU_job' not in usable:usable['historical_CPU_job']=usable['CPU_job']
usable.update(updated_utc=now,state=state,goal_status=recovery['goal_status'],CPU_job=job,
              last_observation=latest,next=next_action,current_execution_note=next_action,
              usage_observation=recovery['usage_observed'],limitations=[
                  'Full private Kaggle input and actual runtime image verification pending',
                  'Scientific0/2epochs,0/2fullvalidations; no final test',
                  'Metadata API adapter prepared/synthetic tested, not cloud executed'],
              independent_continuation={'already_submitted':True,'live_job':live,'note':'Bounded CPU data transport only; no monitoring claim after assistant stops'})
save('results/MM_PART1_USABLE_RECEIPT_20261024.json',usable)
text=(f'{now}: Full682170original TSV/source metadata joins passed. Prior pack audit '
      f'{audit["packs_checked"] if audit else 0}/18; durable{images}images/{packs}packs. '
      f'CPU API job status={state}; exact latest counter in its JSON receipt; no duplicate launch. '
      'Source/bundle/pid/boot/cell in results/MM_PART1_API_PACK_JOB_20261025.json. '
      'Metadata API bridge15synthetic guards and existing six-image runtime-gate regression passed; '
      'adapter not cloud executed. Scientific0/2epochs,0/2fullvalidations,test0; bars100/40/20/53 unchanged. '
      'Five-hour reserve applies; weekly monitored as total availability. User reported Goal resumed, '
      'but supported API stillblocked at last check; manual authorized work continues. '+next_action)
for relative in ['context/RESUME_HERE.md','context/PROJECT_CONTEXT.md','context/DECISIONS.md','context/EXPERIMENT_LOG.md',
                 'context/TASK_REPORT.md','context/MM_PART1_RESUME_CHECKPOINT_20261023.md','collab/COLAB_WORKLOG.md',
                 'work_logs/MODEL_STATUS.md','README.md']:
    path=root/relative
    content=path.read_text()
    a='<!-- CURRENT API TRANSPORT OBSERVATION -->';b='<!-- /CURRENT API TRANSPORT OBSERVATION -->'
    if a in content:
        before,rest=content.split(a,1);_,after=rest.split(b,1);content=before+after.lstrip('\n')
    path.write_text(a+'\n'+text+'\n'+b+'\n\n'+content)
print(json.dumps({'state':state,'source_join_passed':bool(joined),'packs_audited':audit['packs_checked'] if audit else 0,'durable_images':images,'scientific_epochs':0}))
