"""Independent preregistered faults; failures in test infrastructure never score."""
import pathlib,json,subprocess,sys,os,shutil,xml.etree.ElementTree as ET
from j4_stage import run_http,NAME
cfg=json.loads(pathlib.Path('j4_config.json').read_text())
mut=json.loads(pathlib.Path('j4_mutations.json').read_text())
if pathlib.Path('j4_seed_index').exists():mut=[mut[int(pathlib.Path('j4_seed_index').read_text())]]
results=[]
for name,file,old,new in mut:
 p=pathlib.Path(file);original=p.read_text();assert old in original,(name,'missing mutation target')
 dest=pathlib.Path('seed-evidence')/name;dest.mkdir(parents=True,exist_ok=True)
 try:
  p.write_text(original.replace(old,new,1))
  if NAME=='vue':
   cmd=['yarn','test','--runInBand','--json','--outputFile='+str(dest/'tests.json')]
  elif NAME=='fastapi':
   cmd=['poetry','run','python','-m','pytest','-n','2','--junitxml='+str(dest/'tests.xml')]
  else:
   shutil.rmtree('target/surefire-reports',ignore_errors=True)
   cmd=['./mvnw','-B','package','-Dspring-javaformat.skip=true']
  with (dest/'tests.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300)
  if NAME=='vue':
   d=json.loads((dest/'tests.json').read_text())
   assert d['numTotalTests']==cfg['test_count'] and d['numPendingTests']==0 and d['numRuntimeErrorTestSuites']==0,'test inventory or infrastructure error'
   failed=d['numFailedTests']
  else:
   files=[dest/'tests.xml'] if NAME=='fastapi' else list(pathlib.Path('target/surefire-reports').glob('TEST-*.xml'))
   cases=[c for f in files for c in ET.parse(f).findall('.//testcase')]
   assert len(cases)==cfg['test_count'],'test inventory changed'
   assert not any(c.find('error') is not None or c.find('skipped') is not None for c in cases),'test runtime/infra error or skip'
   failed=sum(c.find('failure') is not None for c in cases)
   if NAME=='spring':
    for f in files:shutil.copy(f,dest/f.name)
  assert r.returncode==0 or failed>0,'build/infra failure'
  if NAME=='vue':
   pathlib.Path('components.actual.json').unlink(missing_ok=True)
   env=os.environ.copy();env['BABEL_ENV']='test'
   with (dest/'components.log').open('w') as log:
    h=subprocess.run(['yarn','jest','--runInBand','--testMatch','**/j4.characterize.spec.js','--json','--outputFile='+str(dest/'components-tests.json')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90)
   d=json.loads((dest/'components-tests.json').read_text())
   assert d['numTotalTests']==1 and d['numRuntimeErrorTestSuites']==0 and pathlib.Path('components.actual.json').exists(),'component harness infrastructure error'
   detected=d['numFailedTests']>0;shutil.copy('components.actual.json',dest/'components.json')
  else:
   if NAME=='spring' and failed:
    # Build the altered resource artifact after an assertion failure, without treating this as passing tests.
    with (dest/'package.log').open('w') as log:subprocess.run(['./mvnw','-B','package','-DskipTests','-Dspring-javaformat.skip=true'],stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
   detected=run_http(dest,strict=False)
  results.append({'fault':name,'project_detected':failed>0,'project_failures':failed,'harness_detected':detected})
  pathlib.Path('seed-results.json').write_text(json.dumps(results,indent=2))
 finally:p.write_text(original)
print(json.dumps(results,indent=2))
if len(results)==5:
 a=sum(x['project_detected'] for x in results);b=sum(x['project_detected'] or x['harness_detected'] for x in results)
 assert b>=4 and 5-b<=(5-a)/2,'seed threshold missed'
