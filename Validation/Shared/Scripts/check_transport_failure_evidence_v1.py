"""Fault-inject Drive/scratch writes; no data preparation or cloud execution."""
import contextlib,hashlib,importlib.util,io,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'collab'))
spec=importlib.util.spec_from_file_location('transport_v4',ROOT/'collab/run_usable_transport_job_v4.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
with tempfile.TemporaryDirectory(dir=ROOT/'data',prefix='transport-failure-check-') as temp:
 root=Path(temp);real=t.prep.record
 def case(name,fail_drive=False,fail_scratch=False):
  failure={'job_id':name,'state':'approved_usable_transport_failed','error':'ORIGINAL_DRIVE_READ_ERROR_107','traceback':'original source-read traceback','training':False}
  drive=root/(name+'_drive.json');scratch=root/(name+'_scratch')
  def injected(path,value):
   if Path(path)==drive and fail_drive:raise OSError(107,'simulated disconnected Drive')
   if Path(path).parent==scratch and fail_scratch:raise OSError(28,'simulated scratch write failure')
   return real(path,value)
  t.prep.record=injected;out=io.StringIO()
  with contextlib.redirect_stdout(out):result=t.publish_failure(failure,drive,scratch)
  events=[json.loads(x) for x in out.getvalue().splitlines()]
  assert events[0]==failure,'Original exception was hidden by failure writer'
  assert result['drive_saved'] is (not fail_drive)
  assert result['scratch_saved'] is (not fail_scratch)
  assert result['scratch_is_durable'] is False
  if not fail_drive:assert json.loads(drive.read_text())==failure
  if not fail_scratch:
   local=scratch/(name+'_failure.json');assert json.loads(local.read_text())==failure
   assert result['scratch_sha256']==hashlib.sha256(local.read_bytes()).hexdigest()
  return result
 cases=[case('success'),case('drive_failure',True),case('scratch_failure',False,True),case('both_fail',True,True)]
 t.prep.record=real
 # Immutable prior evidence must not be overwritten by a duplicate writer.
 original={'job_id':'immutable','error':'first exception'}
 drive=root/'immutable_drive.json';real(drive,original)
 with contextlib.redirect_stdout(io.StringIO()):duplicate=t.publish_failure({'job_id':'immutable','error':'later exception'},drive,root/'immutable_scratch')
 assert duplicate['drive_saved'] is False and json.loads(drive.read_text())==original
receipt={'status':'passed_transport_failure_fault_checks','cases':5,'original_exception_printed_before_all_writes':True,'both_destinations_failing_does_not_hide_original_error':True,'immutable_existing_evidence_not_overwritten':True,'scratch_never_claimed_durable':True,'cloud_execution':False,'training':False,'runner_sha256':hashlib.sha256((ROOT/'collab/run_usable_transport_job_v4.py').read_bytes()).hexdigest()}
(ROOT/'results/transport_failure_evidence_checks_20261024.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
