"""Build CP866 TASM sources with JWasm."""
from pathlib import Path
import hashlib
import os
import re
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import make1125

def code_part(line):
    quoted = None
    for i, c in enumerate(line):
        if c == quoted:
            quoted = None
        elif quoted is None:
            if c in "\"'":
                quoted = c
            elif c == ';':
                return line[:i]
    return line

def translate(source, destination):
    lines = []
    def include(path):
        for line in path.read_bytes().decode('cp866').splitlines():
            m = re.match(r'\s*include\s+(\S+)', line, re.I)
            if m:
                include(path.parent / m[1].upper())
            else:
                lines.append(line)
    include(source)
    aliases = {}
    for line in lines:
        m = re.match(r'\s*(\w+)\s+equ\s+(word|byte)\s+ptr\s+ds:\[([^]]+)\]', code_part(line), re.I)
        if m: aliases[m[1].lower()] = (m[2], m[3])
    scopes = [dict(parent=None, name='root', labels=set())]
    current = 0
    tagged = []
    for line in lines:
        code = code_part(line)
        proc = re.match(r'\s*(\w+)\s+proc\b', code, re.I)
        end = re.match(r'\s*(\w+)\s+endp\b', code, re.I)
        if proc:
            scopes.append(dict(parent=current, name=proc[1], labels=set()))
            current = len(scopes)-1
            line = proc[1] + ' label near'
        label = re.match(r'\s*(@@\w+)\s*(?::|equ\b|db\b|dw\b|CallNear\b)', code, re.I)
        if label:
            scopes[current]['labels'].add(label[1].lower())
        tagged.append((line, current))
        if end:
            tagged[-1] = ('', current)
            current = scopes[current]['parent']
    output = ['option casemap:all', 'option ljmp']
    for line, scope in tagged:
        code = code_part(line)
        if re.match(r'\s*locals\b', code, re.I) or code.startswith(chr(9608)) or code.startswith('BuildProgram :'):
            continue
        def local(m):
            n = scope
            while n is not None:
                if m[0].lower() in scopes[n]['labels']:
                    return scopes[n]['name'] + '__' + m[0][2:]
                n = scopes[n]['parent']
            raise ValueError(f'Unresolved {m[0]} in {scopes[scope]["name"]}: {line}')
        code = re.sub(r'@@\w+', local, code)
        # TASM outer segment overrides take precedence over the DS in an EQU.
        alias_def = re.match(r'\s*(\w+)\s+equ\b', code, re.I)
        if alias_def and alias_def[1].lower() in aliases:
            code = alias_def[1] + ' equ ' + aliases[alias_def[1].lower()][1]
        else:
            pattern = r'(?<![\w])(?:(es|cs|ds|ss):)?(' + '|'.join(aliases) + r')(?![\w])'
            def memory(m):
                size, address = aliases[m[2].lower()]
                return f'{size} ptr {m[1] or "ds"}:[{address}]'
            code = re.sub(pattern, memory, code, flags=re.I)
        label_prefix = re.match(r'\s*(\w+:)\s*', code)
        if label_prefix:
            output.append(label_prefix[1])
            code = code[label_prefix.end():]
        multi = re.fullmatch(r'\s*(push|pop)\s+((?:(?:ax|bx|cx|dx|si|di|bp|sp|ds|es|ss|cs)\s+)+(?:ax|bx|cx|dx|si|di|bp|sp|ds|es|ss|cs))\s*', code, re.I)
        if multi:
            output.extend(f'\t{multi[1]} {r}' for r in multi[2].split())
        else:
            output.append(code)
    destination.write_bytes(('\r\n'.join(output)+'\r\n').encode('cp866'))

def read_symbols(path):
    listing = Path(path).read_bytes().decode('cp866')
    symbols = {m[1].lower(): int(m[2], 16) for m in re.finditer(
        r'^([A-Za-z_]\w*)[ .]+(?:L Near|Byte(?:\[\d+\])?|Word|DWord|Number)\s+([A-Fa-f0-9]+)h', listing, re.M)}
    if not symbols:
        symbols = {m[1].lower(): int(m[2], 16) for m in re.finditer(
            r'^([A-Za-z_]\w*)\s+(?:Near16|Byte|Word|Dword|Number)\s+(?:CODE:)?\[?([0-9A-F]+)\]?\s*$', listing, re.M)}
    assert 'fonttable' in symbols and 'curverlo' in symbols, 'Unrecognized assembler listing'
    return symbols


FIX2_ZIP = ROOT.parent / 'keyrus_fix2.zip'
PATCHES = [ROOT.parent / 'patches' / 'FIX3.diff', ROOT.parent / 'patches' / 'FIX4.diff']


def fix2_sources():
    """kr8b_src of keyrus_fix2.zip (original v8.0b16, PATCH_FIX1, PATCH_FIX2) checked by fix2.sha256."""
    assert FIX2_ZIP.is_file(), f'{FIX2_ZIP} not found, see README.md'
    expected = {path: digest for digest, path in (l.split() for l in (ROOT / 'fix2.sha256').read_text().splitlines())}
    with zipfile.ZipFile(FIX2_ZIP) as z:
        names = {n.lower().split('kr8b_src/')[-1]: n for n in z.namelist() if 'kr8b_src/' in n.lower()}
        files = {}
        for path, digest in expected.items():
            assert path.lower() in names, f'{FIX2_ZIP.name}: kr8b_src/{path} not found'
            files[path] = z.read(names[path.lower()])
            assert hashlib.sha256(files[path]).hexdigest() == digest, f'{FIX2_ZIP.name}: kr8b_src/{path} is not FIX2'
    return files


def stage(out, cp1125=False, baseline=False):
    """Write FIX2 sources to out, apply FIX3/FIX4 diffs (baseline: test-only diff), cp1125 fonts."""
    files = fix2_sources()
    for layer in ['', 'PATCH_FIX1/', 'PATCH_FIX2/']:
        for path, data in files.items():
            name = path[len(layer):]
            if path.startswith(layer) and '/' not in name:
                (out / name).write_bytes(data)
    # out is inside this repository: stop git from finding it, so git apply works like patch
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(out.resolve().parent))
    for diff in [ROOT / 'baseline.diff'] if baseline else PATCHES:
        subprocess.run(['git', 'apply', '--whitespace=nowarn', str(diff)], cwd=out, env=env, check=True)
    if cp1125:
        make1125.build_fonts(out)


def main():
    baseline = '--baseline' in sys.argv
    out = ROOT / ('build_baseline' if baseline else 'build')
    source = out / 'src'
    source.mkdir(parents=True, exist_ok=True)
    stage(source, baseline=baseline)
    translate(source/'KEYRUS.ASM', out/'KEYRUS.ASM')
    subprocess.run([str(ROOT/'tools/jwasm/JWasm.exe'), '-bin', '-Zm', '-FlKEYRUS.LST', '-FoKEYRUS.COM', 'KEYRUS.ASM'], cwd=out, check=True)
if __name__ == '__main__':
    main()
