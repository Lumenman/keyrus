"""Run the integration batch in an isolated DOSBox mount (Windows)."""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dosbox',default='D:/DOSBox-X/dosbox-x.exe')
    ap.add_argument('--tasm',action='store_true')
    args=ap.parse_args()
    dos=ROOT/'dos_test'
    for name in ['PROBE','HOOK']:
        subprocess.run([str(ROOT/'tools/jwasm/JWasm.exe'),'-bin','-Fo'+name+'.COM',name+'.ASM'],cwd=dos,check=True)
    shutil.copy2(ROOT/('build_tasm' if args.tasm else 'build')/'KEYRUS.COM',dos/'KEYRUS.COM')
    subprocess.run([sys.executable,str(ROOT/'build.py'),'--baseline'],check=True)
    shutil.copy2(ROOT/'build_baseline/KEYRUS.COM',dos/'BASE.COM')
    (dos/'LONG.CFG').write_bytes(b'/'+b'A'*300)
    (dos/'OVER.CFG').write_bytes(b'A'*2049)
    (dos/'BIG.KBD').write_bytes(bytes(65536+318))
    for name in ['DONE.TXT','FAILURES.TXT']:
        (dos/name).unlink(missing_ok=True)
    config=dos/'run.conf'
    config.write_text('[sdl]\nfullscreen=false\noutput=surface\nwaitonerror=false\n[dosbox]\nworking directory option=noprompt\n[cpu]\ncycles=fixed 15000\n[autoexec]\nmount c "'+str(dos)+'"\nc:\nrun.bat\n',encoding='ascii')
    startup=subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow=0
    subprocess.run([args.dosbox,'-conf',str(config),'-noconsole'],cwd=dos,startupinfo=startup,timeout=60,check=True)
    assert (dos/'DONE.TXT').read_text().strip()=='DONE','DOS batch did not finish'
    errors=(dos/'FAILURES.TXT').read_text()
    assert 'FAIL' not in errors, errors
    for n in [2,10,13,16,19,24,27,33,36,39,42]:
        assert (dos/f'T{n:02}.TXT').read_text().strip()=='PASS',f'API probe {n} failed'
    assert '/SCAN=54' in (dos/'T31.TXT').read_text()
    assert '/Alt ignored' in (dos/'T45.TXT').read_text()
    out=(dos/'T48.TXT').read_text()
    assert '/Alt' in out and 'ignored' not in out, out
    print('49 DOS integration cases: PASS')

if __name__=='__main__':main()
