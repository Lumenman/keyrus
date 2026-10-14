"""Check KEYR1125.COM: same as KEYRUS.COM except glyphs F2h-F9h of the three fonts."""
from pathlib import Path
import sys
import make1125 as build

root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'dev'))
from build import read_symbols
original=(root/'dev/build_tasm/KEYRUS.COM').read_bytes()
converted=(root/'dev/build_tasm1125/KEYRUS.COM').read_bytes()
symbols=read_symbols(root/'dev/build_tasm/KEYRUS.LST')
assert len(original)==len(converted)
allowed=set()
for height,name in [(8,'font_8'),(14,'font_14'),(16,'font_16')]:
    start=symbols[name]-256+1
    old=original[start:start+256*height]
    for code,bits in build.cp1125_glyphs(old,height).items():
        at=start+code*height
        assert converted[at:at+height]==bits
        allowed.update(range(at,at+height))
    print(f'8x{height}: all eight CP1125 glyphs verified')
assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,converted)))
assert converted[symbols['rangeflag']-256]==3
assert converted[symbols['comprflag']-256]==0
for name,tables in [('UAL1125.KBD',[0,1]),('URL1125.KBD',[2,3])]:
    data=(root/name).read_bytes()
    assert len(data)==318
    for table,changes in zip(tables,[build.UKR_LOWER,build.UKR_UPPER]):
        for key,code in changes.items(): assert data[table*53+build.KEYS.index(key)]==code
print('Only CP1125 glyphs differ; /ALL enabled; both layouts verified')
