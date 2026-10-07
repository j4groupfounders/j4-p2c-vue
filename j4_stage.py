"""Scoped HTTP replay with owned process cleanup, no external APIs."""
import pathlib,subprocess,os,signal,json,sys
NAME=json.loads(pathlib.Path('j4_config.json').read_text())['name']
def run_http(dest,strict=True):
 dest=pathlib.Path(dest);dest.mkdir(parents=True,exist_ok=True)
 cmd={'fastapi':['poetry','run','uvicorn','app.main:app','--host','127.0.0.1','--port','3000'],
      'spring':['java','-jar',str(next(pathlib.Path('target').glob('*.jar'))),'--server.port=3000'] if NAME=='spring' else [],
      'vue':['yarn','serve','--port','3000']}[NAME]
 pathlib.Path('surface.actual.json').unlink(missing_ok=True)
 with (dest/'boot.log').open('w') as log:
  server=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   with (dest/'probe.log').open('w') as log2:
    probe=subprocess.run([sys.executable,'j4_probe.py'],stdout=log2,stderr=subprocess.STDOUT,timeout=95)
   assert pathlib.Path('surface.actual.json').exists(),'server/probe infrastructure failure'
   surface=json.loads(pathlib.Path('surface.actual.json').read_text())
   assert all(r['status']<500 for r in surface),'server runtime error, not scored as detection'
   (dest/'surface.json').write_text(json.dumps(surface,indent=2))
   if strict:assert probe.returncode==0,'characterization drift'
   return probe.returncode!=0
  finally:
   try:os.killpg(server.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   server.wait(timeout=20)
if __name__=='__main__':run_http('http-evidence')
