"""Native TASM 5.4 assembly; DOS TLINK runs inside an isolated DOSBox mount."""
from pathlib import Path
import argparse
import shutil
import subprocess
from build import stage
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tools',type=Path,default=ROOT.parent/'TASM')
    ap.add_argument('--dosbox',default='D:/DOSBox-X/dosbox-x.exe')
    ap.add_argument('--cp1125',action='store_true',help='also apply PATCH_CP1125 (KEYR1125.COM)')
    ap.add_argument('--publish',action='store_true',help='copy the COM into the repository root')
    args=ap.parse_args()
    out=ROOT/('build_tasm1125' if args.cp1125 else 'build_tasm');out.mkdir(exist_ok=True)
    stage(out,args.cp1125)
    result=subprocess.run([str(args.tools.resolve()/'TASM32r.EXE'),'/m5','/jJUMPS','/dTASM_BUILD','/l','/z','KEYRUS.ASM'],cwd=out,capture_output=True)
    (out/'ASSEMBLE.LOG').write_bytes(result.stdout+result.stderr)
    print((result.stdout+result.stderr).decode('cp866',errors='replace'))
    result.check_returncode()
    for name in ['TLINK.EXE','RTM.EXE','DPMI16BI.OVL']:shutil.copy2(args.tools/name,out/name)
    for name in ['RESULT.TXT','KEYRUS.COM']: (out/name).unlink(missing_ok=True)
    (out/'LINK.BAT').write_bytes(b'@echo off\r\ntlink /t /x keyrus.obj,keyrus.com,keyrus.map > LINK.LOG\r\nif errorlevel 1 echo FAIL > RESULT.TXT\r\nif not errorlevel 1 echo PASS > RESULT.TXT\r\nexit\r\n')
    config=out/'link.conf'
    config.write_text('[sdl]\nfullscreen=false\noutput=surface\nwaitonerror=false\n[dosbox]\nworking directory option=noprompt\n[autoexec]\nmount c "'+str(out)+'"\nc:\nlink.bat\n',encoding='ascii')
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    subprocess.run([args.dosbox,'-conf',str(config),'-noconsole'],cwd=out,startupinfo=startup,timeout=60,check=True)
    assert (out/'RESULT.TXT').read_text().strip()=='PASS',(out/'LINK.LOG').read_text()
    assert (out/'KEYRUS.COM').is_file()
    print((out/'LINK.LOG').read_text())
    print('TASM COM:',(out/'KEYRUS.COM').stat().st_size,'bytes')
    if args.publish:
        name='KEYR1125.COM' if args.cp1125 else 'KEYRUS.COM'
        shutil.copy2(out/'KEYRUS.COM',ROOT.parent/name)

if __name__=='__main__':main()
