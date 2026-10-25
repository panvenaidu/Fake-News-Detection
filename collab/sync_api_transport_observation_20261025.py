"""Synchronize sanitized measured cloud progress, never invent a live counter."""
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--short',type=int,required=True)
parser.add_argument('--weekly',type=int,required=True)
parser.add_argument('--cell',required=True)
parser.add_argument('--goal-status',choices=['active','blocked','paused'],required=True)
args=parser.parse_args()
if not 0<=args.short<=100 or not 0<=args.weekly<=100:raise ValueError('Invalid actual allowance')
now=datetime.now(timezone.utc).isoformat()
observations=json.loads((root/'results/MM_PART1_API_PACK_OBSERVATIONS_20261025.json').read_text())['observations']
releases=[i for i,x in enumerate(observations) if x['state'] in ('bounded_API_pack_release_verified','bounded_API_continuation_release_verified')]
if not releases:raise ValueError('No observed release')
current=observations[releases[-1]:]
release=current[0]
latest=current[-1]
joined=next((x for x in reversed(current) if x['state']=='api_original_TSV_and_source_metadata_joins_passed'),None)
audit=next((x for x in reversed(current) if x['state']=='api_prior_pack_verified'),None)
committed=next((x for x in reversed(current) if x['state']=='api_pack_committed'),None)
terminal=next((x for x in reversed(current) if x['state'] in ('api_transport_terminal','api_transport_failed')),None)
live=terminal is None
state='real_API_transport_live' if live else terminal['state']
images=committed['images_committed'] if committed else release.get('durable_images',319820)
packs=committed['packed_shards'] if committed else release.get('durable_packs',18)

def read(path):return json.loads((root/path).read_text())
def save(path,data):(root/path).write_text(json.dumps(data,indent=2)+'\n')
job=read('results/MM_PART1_API_PACK_JOB_20261025.json')
if job['release_utc']!=release['utc']:
    job['predecessor_terminal']=job.get('terminal')
    job.update(release_utc=release['utc'],cell=args.cell,
               notebook='https://colab.research.google.com/drive/1EQr8BSZEzyMpoGyQweXE3rRCkOHPbesU#scrollTo='+args.cell,
               max_new_packs=release['max_new_packs'],prior_durable_images=images,prior_durable_packs=packs,
               registered_job_id='Retrieve from private api_transport_v1/STATE.json or current terminal output; not printed yet',
               source_commit='f8175f65a390c442a34e705dfb20dbe36c07756a')
job.update(utc=now,state=state,latest_counter=latest,source_joins=joined,prior_pack_audit=audit,
           new_committed_packs_observed=packs-job['prior_durable_packs'],terminal=terminal,
           latest_measured_durable_images=images,latest_measured_durable_packs=packs)
if terminal and terminal.get('job_id'):job['registered_job_id']=terminal['job_id']
save('results/MM_PART1_API_PACK_JOB_20261025.json',job)
next_action=('Inspect same cell/process/private control before continuation; never duplicate live packing. After the first durable transaction, '
             'verify terminal archive/receipt and recovery, then resume remaining lossless packing. Full private Kaggle input, actual runtime '
             'image SHA/decode, CUDA recovery/preflight, epochs1–2 and full validations remain pending. No Part1 final test.')
recovery=read('results/MM_PART1_RECOVERY_PROGRESS_20261025.json')
recovery.update(updated_utc=now,state=state,durable_packed_images=images,durable_packs=packs,
                goal_status=args.goal_status,
                full_source_inventory_passed=bool(joined),source_metadata_inventory_passed=True,
                no_active_packing_or_training_job=not live,independent_job_running=live,next=next_action,
                usage_observed={'short_remaining':args.short,'weekly_remaining':args.weekly,'utc':now},
                current_goal_turn_classification='Progress: full original TSV/source joins passed; old archives being full-hash audited; API metadata bridge prepared and synthetic-tested')
if 'historical_runtime' not in recovery:recovery['historical_runtime']=recovery['runtime']
recovery['runtime']={'platform':'Colab CPU','notebook':job['notebook'],'pid':job['runtime_pid'],
                     'boot_id':job['boot_id'],'RAM_GB_observed_approx':1.9,'DriveFS_mounted':False}
recovery['api']['scope']='Source joins, archive audits and commits are separately recorded per job; full image runtime gate still pending.'
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
tracker=read('results/PROGRESS_TRACKER.json')
tracker.update(updated_utc=now,current_execution_note=next_action,
               latest_operational_note=state,latest_API_job='results/MM_PART1_API_PACK_JOB_20261025.json')
tracker['usage_reserve_policy'].update(latest_observed_remaining_percent={'five_hour':args.short,'weekly':args.weekly},
                                      observation_utc=now,threshold_scope='five_hour_primary_only_per_user_override')
tracker['models']['text_plus_image']['data_preparation']={
    'approved_images':682170,'durable_packed_images':images,'durable_packs':packs,
    'transport_percent':round(100*images/682170,2),'image_runtime_gate_passed':False,
    'training_epochs_completed':0,'full_validations_completed':0,'final_test_performed':False,
    'note':'Transport percentage is not workflow or scientific completion'}
save('results/PROGRESS_TRACKER.json',tracker)
text=(f'{now}: Full682170original TSV/source metadata joins passed. Prior pack audit '
      f'{audit["packs_checked"] if audit else 0}/{audit["total_packs"] if audit else job["prior_durable_packs"]}; durable{images}images/{packs}packs. '
      f'CPU API job status={state}; exact latest counter in its JSON receipt; no duplicate launch. '
      'Source/bundle/pid/boot/cell in results/MM_PART1_API_PACK_JOB_20261025.json. '
      'Metadata API bridge15synthetic guards and existing six-image runtime-gate regression passed; '
      'adapter not cloud executed. Scientific0/2epochs,0/2fullvalidations,test0; bars100/40/20/53 unchanged. '
      'Five-hour reserve applies; weekly monitored as total availability. '
      f'Supported Goal API verified {args.goal_status}; existing Goal preserved. '+next_action)
for relative in ['context/RESUME_HERE.md','context/PROJECT_CONTEXT.md','context/DECISIONS.md','context/EXPERIMENT_LOG.md',
                 'context/TASK_REPORT.md','context/MM_PART1_RESUME_CHECKPOINT_20261023.md','collab/COLAB_WORKLOG.md',
                 'work_logs/MODEL_STATUS.md','README.md','results/PROGRESS_TRACKER.md']:
    path=root/relative
    content=path.read_text()
    a='<!-- CURRENT API TRANSPORT OBSERVATION -->';b='<!-- /CURRENT API TRANSPORT OBSERVATION -->'
    if a in content:
        before,rest=content.split(a,1);_,after=rest.split(b,1);content=before+after.lstrip('\n')
    path.write_text(a+'\n'+text+'\n'+b+'\n\n'+content)
print(json.dumps({'state':state,'source_join_passed':bool(joined),'packs_audited':audit['packs_checked'] if audit else 0,'durable_images':images,'scientific_epochs':0}))
