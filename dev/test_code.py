"""Execute KEYRUS machine code with Unicorn and deterministic DOS fault injection."""
from pathlib import Path
import re
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parent
import sys
from build import read_symbols
BUILD=ROOT/('build_tasm' if '--tasm' in sys.argv else 'build')
BINARY=(BUILD/'KEYRUS.COM').read_bytes()
SYM=read_symbols(BUILD/'KEYRUS.LST')

REG={n:globals()['UC_X86_REG_'+n.upper()] for n in ['ax','bx','cx','dx','si','di','bp','sp','cs','ds','es','ss','ip','al','ah','bl','bh']}

class Machine:
    def __init__(self):
        self.u=Uc(UC_ARCH_X86,UC_MODE_16)
        self.u.mem_map(0,0x100000)
        self.u.mem_write(0x10100,BINARY)
        for r in ['cs','ds','es','ss']: self.set(r,0x1000)
        self.set('sp',0xf000)
        self.exit=None; self.files={}; self.handles={}; self.next_handle=5
        self.fail={}; self.calls=[]; self.output=bytearray(); self.dos_override=None
        self.u.hook_add(UC_HOOK_INTR,self.interrupt)
        self.u.hook_add(UC_HOOK_CODE,self.code)
    def get(self,r): return self.u.reg_read(REG[r])
    def set(self,r,v): self.u.reg_write(REG[r],v)
    def addr(self,name): return 0x10000+SYM[name.lower()]
    def put(self,name,v,size=2): self.u.mem_write(self.addr(name),v.to_bytes(size,'little'))
    def value(self,name,size=2): return int.from_bytes(self.u.mem_read(self.addr(name),size),'little')
    def word(self,a,v): self.u.mem_write(a,struct.pack('<H',v))
    def string(self,a):
        b=bytearray()
        while self.u.mem_read(a,1)!=b'\0':
            b.extend(self.u.mem_read(a,1)); a+=1
            assert len(b)<1024
        return b.decode('ascii').upper()
    def cf(self,v):
        f=self.u.reg_read(UC_X86_REG_EFLAGS)
        self.u.reg_write(UC_X86_REG_EFLAGS,(f&~1)|bool(v))
    def error(self,ax=5): self.set('ax',ax); self.cf(True)
    def code(self,u,address,size,data):
        if address==self.addr('Exit'):
            self.exit=self.get('al'); u.emu_stop()
    def run(self,name,limit=1000000):
        self.word(0x10000+self.get('sp')-2,0xfff0)
        self.set('sp',self.get('sp')-2)
        self.u.emu_start(self.addr(name),0x1fff0,count=limit)
        assert self.exit is not None or self.get('ip')==0xfff0, (name,'instruction limit',hex(self.get('ip')))
    def interrupt(self,u,n,data):
        ax=self.get('ax'); ah=ax>>8; al=ax&255
        self.calls.append((n,ax))
        if self.dos_override and self.dos_override(n,ax): return
        if n==0x16:
            if ax==0x4100:
                self.set('ax',0xaaaa); self.set('cx',0x4b52); self.set('bx',0x800+SYM['curverlo']); self.set('dx',0x3000); return
            raise AssertionError(('INT16',hex(ax)))
        assert n==0x21,(n,ax)
        self.cf(False)
        src=self.get('ds')*16+self.get('dx'); dst=self.get('es')*16+self.get('di')
        if ah in (2,9):
            if ah==2: self.output.append(self.get('dx')&255)
            else:
                while self.u.mem_read(src,1)!=b'$': self.output.extend(self.u.mem_read(src,1)); src+=1
            return
        if ah in (0x35,0x25):
            if ah==0x35:
                v=bytes(self.u.mem_read(al*4,4)); off,seg=struct.unpack('<HH',v)
                self.set('bx',off); self.set('es',seg)
            else: self.u.mem_write(al*4,struct.pack('<HH',self.get('dx'),self.get('ds')))
            return
        if ah==0x49: return
        op={0x3d:'open',0x3c:'create',0x5b:'exclusive',0x3f:'read',0x40:'write',0x3e:'close',0x42:'seek',0x43:'attr',0x56:'rename',0x41:'delete'}.get(ah)
        assert op,(hex(ax),'unhandled DOS')
        count=self.fail.get(op,0)
        if count:
            self.fail[op]=count-1
            return self.error()
        if op in ['open','create','exclusive','attr','rename','delete']: name=self.string(src)
        if op in ['open','create','exclusive']:
            if op=='open' and name not in self.files: return self.error(2)
            if op=='exclusive' and name in self.files: return self.error(80)
            if op!='open': self.files[name]=bytearray()
            h=self.next_handle; self.next_handle+=1; self.handles[h]=[name,0]; self.set('ax',h)
        elif op=='attr':
            if name not in self.files: return self.error(2)
            if al==0: self.set('cx',0x20)
        elif op=='rename':
            new=self.string(dst)
            if name not in self.files: return self.error(2)
            if new in self.files: return self.error(5)
            if self.fail.get('rename_to_original') and name.endswith('.TMP'):
                self.fail['rename_to_original']=False; return self.error()
            self.files[new]=self.files.pop(name)
        elif op=='delete':
            if name not in self.files: return self.error(2)
            del self.files[name]
        elif op=='close': self.handles.pop(self.get('bx'),None)
        else:
            name,pos=self.handles[self.get('bx')]; content=self.files[name]
            if op=='seek':
                delta=(self.get('cx')<<16)|self.get('dx')
                pos=delta+(len(content) if al==2 else pos if al==1 else 0)
                self.set('ax',pos&65535); self.set('dx',pos>>16)
            elif op=='read':
                size=min(self.get('cx'),len(content)-pos)
                if self.fail.get('short_read'): size=max(0,size-1)
                self.u.mem_write(src,bytes(content[pos:pos+size])); self.set('ax',size); pos+=size
            elif op=='write':
                size=0 if self.fail.get('short_write') else self.get('cx')
                content[pos:pos+size]=self.u.mem_read(src,size); self.set('ax',size); pos+=size
            self.handles[self.get('bx')][1]=pos

def test_parameters():
    for length in [254,255,256,300]:
        m=Machine(); m.put('Buffer2',0xd100); m.put('ComLineSeg',0x3000); m.put('ComLineLength',length)
        m.u.mem_write(0x30000,b'A'*length); m.u.mem_write(0x1d200,b'Z'*32)
        m.run('ReadPar')
        assert m.exit==(1 if length>255 else None)
        assert bytes(m.u.mem_read(0x1d200,32))==b'Z'*32
    for size in [2048,2049]:
        m=Machine(); m.put('EndProgram',0x6000)
        cmd=b'@A'; m.u.mem_write(0x10080,bytes([len(cmd)])+cmd+b'\r')
        m.files['A']=bytearray(b'A'*size); m.run('PrepareCommandLine')
        assert m.exit==(1 if size>2048 else None)
    m=Machine(); m.put('EndProgram',0x6000); cmd=b' @A @B'
    m.u.mem_write(0x10080,bytes([len(cmd)])+cmd+b'\r')
    m.files['A']=bytearray(b'A'*1500);m.files['B']=bytearray(b'B'*1500)
    m.run('PrepareCommandLine'); assert m.exit==1

    for fault in ['read','close','seek']:
        m=Machine();m.put('EndProgram',0x6000);cmd=b'@A'
        m.u.mem_write(0x10080,bytes([len(cmd)])+cmd+b'\r')
        m.files['A']=bytearray(b'/FAST=OFF');m.fail[fault]=1
        m.run('PrepareCommandLine');assert m.exit==1

def test_delay():
    m=Machine();m.set('es',0x3000);m.set('di',0x100)
    m.word(0x30053,0x100);m.word(0x3010a,0x200)
    m.u.mem_write(9*4,struct.pack('<HH',0xe987,0xf000))
    m.run('DelayInstall9');assert m.get('es')==0x3000 and m.get('di')==0x100
    assert bytes(m.u.mem_read(9*4,4))==struct.pack('<HH',0x200,0x3000)

def test_no_fonts():
    m=Machine();m.set('es',0x3000);m.set('di',0x100);m.word(0x30107,0)
    before=bytes(m.u.mem_read(0x30000,0x10000));m.run('AddFonts')
    assert bytes(m.u.mem_read(0x30000,0x10000))==before
    m=Machine();m.set('es',0x3000);m.put('KeybFlag',0,1);m.put('IntFlag',0,1);m.put('Adapter',2,1)
    for flag in ['font_8','font_14','font_16']:m.put(flag,0,1)
    m.run('BuildProgram');assert m.exit==1 and b'No fonts selected' in m.output
    assert not any(n==0x21 and ax>>8==0x25 for n,ax in m.calls)

def resident(m):
    m.word(0x30059,0x200);m.word(0x30057,0x300);m.word(0x30063,0x400);m.word(0x30053,0x100);m.word(0x3010a,0x500)
    for n,off in [(8,0x200),(0x16,0x300),(0x10,0x400),(9,0x500)]: m.u.mem_write(n*4,struct.pack('<HH',off,0x3000))

def test_release():
    for vector in [8,9,0x10,0x16]:
        m=Machine();resident(m);m.word(vector*4,0xabcd)
        before=bytes(m.u.mem_read(0,1024));m.run('Release');assert m.exit==1
        assert bytes(m.u.mem_read(0,1024))==before
        assert not any(n==0x21 and ax>>8 in (0x25,0x49) for n,ax in m.calls)

    m=Machine();resident(m);m.word(0x30055,0x600);m.word(0x30605,0x700)
    expected={}
    for n,entry,old,base in [(8,'Int_08h_Entry','Ofs08',0x200),(0x16,'Int_16h_Entry','Ofs16h',0x300),(9,'Int_09h_Entry','Ofs_09a',0x500),(0x10,'Old_10h_Entry','Ofs10h',0x700)]:
        v=struct.pack('<HH',0x100+n,0xf000)
        m.u.mem_write(0x30000+base+SYM[old.lower()]-SYM[entry.lower()],v)
        expected[n]=v
    m.run('Release');assert m.exit==0
    for n,v in expected.items():assert bytes(m.u.mem_read(n*4,4))==v
    assert (0x21,0x4900) in m.calls or any(n==0x21 and ax>>8==0x49 for n,ax in m.calls)

def test_save():
    original='C:\\KEYRUS.COM'
    for fault in [None,'short_write','write','close','rename','rename_to_original','existing_temp','existing_backup']:
        m=Machine();m.word(0x1002c,0x4000)
        m.u.mem_write(0x40000,b'PATH=C:\\\0\0\x01\0'+original.encode()+b'\0')
        m.put('EndProgram',0x100+len(BINARY));m.files[original]=bytearray(b'original')
        if fault=='existing_temp':m.files['C:\\KR3SAVE.TMP']=bytearray(b'keep')
        elif fault=='existing_backup':m.files['C:\\KR3SAVE.BAK']=bytearray(b'keep')
        elif fault:m.fail[fault]=1
        m.run('SaveMyself')
        if fault:
            assert m.exit==1,(fault,m.exit,m.output)
            assert m.files[original]==b'original',(fault,m.files.keys())
            assert b'Configuration Saved' not in m.output
            if fault=='existing_temp': assert m.files['C:\\KR3SAVE.TMP']==b'keep'
            if fault=='existing_backup': assert m.files['C:\\KR3SAVE.BAK']==b'keep'
        else:
            assert m.exit==0 and len(m.files[original])==len(BINARY)
            assert 'C:\\KR3SAVE.BAK' not in m.files and 'C:\\KR3SAVE.TMP' not in m.files

def test_file_io():
    for routine,size in [('KbdFile',318),('FontFile',4096)]:
        for fault in ['short_read','read','seek','close','oversize']:
            m=Machine();m.set('si',0xd000);m.u.mem_write(0x1d000,b'INPUT\0');m.put('Buffer2',0xd100)
            m.files['INPUT']=bytearray(size+(65536 if fault=='oversize' else 0))
            if fault!='oversize':m.fail[fault]=1
            m.run(routine);assert m.exit==1,(routine,fault,m.exit)
    for fault in ['short_write','write','close']:
        m=Machine();m.fail[fault]=1;m.run('CreateFiles');assert m.exit==2

def test_scan():
    for explicit_lat in [False,True]:
        m=Machine();m.word(0x30053,0x100);m.word(0x30100,54);m.word(0x30102,54 if not explicit_lat else 42)
        m.put('ScanCode',0x9d);m.u.mem_write(m.addr('ComFlags')+3,b'\x01')
        m.run('TryResidentChange');assert m.exit is None
        assert int.from_bytes(m.u.mem_read(0x30100,2),'little')==0x9d
        assert int.from_bytes(m.u.mem_read(0x30102,2),'little')==(42 if explicit_lat else 0x9d)
    m=Machine();m.word(0x30053,0x100);m.word(0x30100,0x9d);m.word(0x30102,42)
    m.put('LatCode',0);m.u.mem_write(m.addr('ComFlags')+5,b'\x01');m.run('TryResidentChange')
    assert int.from_bytes(m.u.mem_read(0x30102,2),'little')==0x9d

def test_alt():
    # AlterCode=+4, KeybMatrixLen=+10h in the keyboard block; 106 bytes: resident has only the Russian matrix, enabling /ALT would read code as a matrix
    for length,alt,expected in [(106,0x38,0xffff),(212,0x38,0x38),(371,0x38,0x38),(106,0,0)]:
        m=Machine();m.word(0x30053,0x100);m.word(0x30100+4,0xffff)
        m.word(0x30100+0x10,length)
        m.put('AltCode',alt);m.u.mem_write(m.addr('ComFlags')+4,b'')
        m.run('TryResidentChange');assert m.exit is None
        assert int.from_bytes(m.u.mem_read(0x30100+4,2),'little')==expected,(length,alt)
        assert (b'/ALT IGNORED' in bytes(m.output).upper())==(expected==0xffff),(length,alt,m.output)

def test_interface_without_indicators():
    m=Machine();m.set('es',0x3000)
    m.put('RangeFlag',0,1);m.put('Adapter',2,1)
    for flag in ['ColorBorder','AltColorBorder','BeepFlag','LampFlag']:m.put(flag,0,1)
    m.run('BuildProgram');assert m.exit is None
    entry=int.from_bytes(m.u.mem_read(0x30057,2),'little')
    for ax,mode in [(0x4190,0),(0x414c,1),(0x4102,2)]:
        m.set('cs',0x3000);m.set('ds',0x1000);m.set('es',0x1000);m.set('sp',0xeff0)
        m.u.mem_write(0x1eff0,struct.pack('<HHH',0xfff0,0x1000,0x202))
        m.set('ax',ax);m.set('bl',6)
        m.u.emu_start(0x30000+entry,0x1fff0,count=100000)
        assert m.get('ip')==0xfff0
        assert m.u.mem_read(0x30007,1)[0]&3==mode

def test_other_build_refused():
    for routine in ['Release','TryResidentChange']:
        m=Machine();resident(m);m.u.mem_write(m.addr('ComFlags')+3,b'\x01');m.put('ScanCode',0x9d)
        before=bytes(m.u.mem_read(0x30000,0x1000));vectors=bytes(m.u.mem_read(0,1024))
        def other(n,ax):
            if n==0x16 and ax==0x4100:
                m.set('ax',0xaaaa);m.set('cx',0x4b52);m.set('dx',0x3000)
                m.set('bx',0x803 if SYM['curverlo']==4 else 0x804)
                return True
            return False
        m.dos_override=other;m.run(routine)
        assert bytes(m.u.mem_read(0x30000,0x1000))==before
        assert bytes(m.u.mem_read(0,1024))==vectors
        if routine=='Release':assert m.exit==1
        else:assert b"can't Change configuration".upper() in bytes(m.output).upper()

if __name__=='__main__':
    for test in [test_parameters,test_delay,test_no_fonts,test_release,test_save,test_file_io,test_scan,test_alt,test_interface_without_indicators,test_other_build_refused]:
        test();print(test.__name__+': PASS')
