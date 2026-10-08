# Leave empty for a fresh attempt. For recovery, paste the exact previous
# ATTEMPT folder printed in the cloud output (never guess the folder).
RESUME_ATTEMPT = ''
command = [sys.executable, '-u', str(remote/'train_official_text.py'), '--config', str(remote/'protocol.json'), '--data', str(data), '--output', str(backup)]
if RESUME_ATTEMPT:
    command += ['--resume-attempt', RESUME_ATTEMPT]
subprocess.run(command, check=True)
