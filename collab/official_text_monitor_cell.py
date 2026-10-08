"""Read-only live monitor for the guarded Chrome Colab launch."""
import json
import time
from IPython.display import clear_output

while True:
    clear_output(wait=True)
    print(current_attempt.name, flush=True)
    for model_name in ('bert-base', 'modernbert-base'):
        folder = current_attempt / model_name
        state_file = folder / 'status.json'
        if not state_file.exists():
            print(model_name, 'queued', flush=True)
            continue
        state = json.loads(state_file.read_text())
        history_file = folder / 'history.json'
        history = json.loads(history_file.read_text()) if history_file.exists() else []
        last = history[-1]['validation'] if history else None
        recovery_file = folder / 'recovery_checkpoint.json'
        recovery = json.loads(recovery_file.read_text()) if recovery_file.exists() else None
        print(model_name, state['state'], 'epoch', state.get('epoch'), 'batch', state.get('step'),
              'updates', state.get('optimizer_updates'), flush=True)
        if recovery:
            print('Saved recovery:', recovery['epoch'], recovery['step'], flush=True)
        if last:
            print('Latest val accuracy/F1:', round(last['accuracy'], 4), round(last['macro_f1'], 4), flush=True)
        if state['state'] == 'failed':
            print('Error:', state['reason'].splitlines()[-1], flush=True)
        if (folder / 'result.json').exists():
            result = json.loads((folder / 'result.json').read_text())
            print('Final test accuracy/F1:', round(result['test']['accuracy'],4), round(result['test']['macro_f1'],4), flush=True)
    return_code = trainer.poll()
    print('Process:', return_code, 'UTC:', time.strftime('%H:%M:%S', time.gmtime()), flush=True)
    if return_code is not None:
        break
    time.sleep(30)
