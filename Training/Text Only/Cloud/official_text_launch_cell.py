# Colab cell: never launch a duplicate trainer after a notebook reconnect.
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# Leave empty for a fresh attempt. Recovery requires the exact saved ATTEMPT path.
RESUME_ATTEMPT = ''
active = []
for process_path in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        arguments = process_path.read_bytes().decode(errors='replace').split('\0')
    except OSError:
        continue
    if any(Path(argument).name == 'train_official_text.py' for argument in arguments if argument):
        active.append(int(process_path.parent.name))
if active:
    raise RuntimeError(f'Existing training process {active}; inspect its status before restarting')

command = [sys.executable, '-u', str(remote/'train_official_text.py'), '--config', str(remote/'protocol.json'), '--data', str(data), '--output', str(backup)]
if RESUME_ATTEMPT:
    resume_path = Path(RESUME_ATTEMPT)
    if resume_path.parent != backup or not (resume_path/'protocol.json').is_file():
        raise ValueError('Use the exact existing attempt inside the permanent output folder')
    command += ['--resume-attempt', str(resume_path)]
existing_attempts = set(backup.glob('OFFICIAL-6W-*'))
launch_stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
launch_log = backup / f'launcher_{launch_stamp}.log'
with launch_log.open('x') as stream:
    trainer = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                               start_new_session=True)
launch_metadata = {'pid': trainer.pid, 'utc': datetime.now(timezone.utc).isoformat(),
                   'command': command, 'log': str(launch_log), 'resume_attempt': RESUME_ATTEMPT}
(backup / f'launch_{launch_stamp}.json').write_text(json.dumps(launch_metadata, indent=2)+'\n')
for _ in range(120):
    created = set(backup.glob('OFFICIAL-6W-*')) - existing_attempts
    if RESUME_ATTEMPT or len(created) == 1:
        current_attempt = Path(RESUME_ATTEMPT) if RESUME_ATTEMPT else created.pop()
        print('ATTEMPT', str(current_attempt), 'PID', trainer.pid, flush=True)
        break
    if trainer.poll() is not None:
        raise RuntimeError(launch_log.read_text()[-1500:])
    time.sleep(1)
else:
    raise RuntimeError(f'Trainer PID {trainer.pid} launched; inspect {launch_log} before any retry')
