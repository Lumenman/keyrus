r"""Build cp1125 (Ukrainian RUSCII) files for KEYRUS 8.0 FIX4.

Creates here:
  UAL1125.KBD   UAL.KBD: Ukrainian / pseudographics / Latin
  URL1125.KBD   URL.KBD: Russian / Ukrainian / Latin
  CP1125.TXT    cp1125 -> Unicode table for DOSBox-X ([dos] customcodepage=1125,<path>)
build_fonts() is called by dev\build_tasm.py --cp1125: FIX1 fonts with glyphs F2h-F9h redrawn
for cp1125 (used in pixel output modes; DOSBox-X TrueType output draws text itself).

Ukrainian layout changes: і/І on S (F7h/F6h, instead of Latin i/I), ї/Ї on ] (F9h/F8h),
є/Є on ' (F5h/F4h), ґ/Ґ on \ (F3h/F2h), apostrophe ' on ` (Shift+` stays ~).
cp1125 differs from cp866 only in F2h-F9h: Ґґ Єє Іі Її instead of Єє Її Ўў °∙.
"""
import os
import unicodedata
import re
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))

# .KBD: 6 tables (3 layouts x lower/upper) of 53 characters for scan codes 01h..35h
KEYS = (['Esc'] + list('1234567890-=') + ['BS', 'Tab'] + list('qwertyuiop[]') + ['Enter', 'Ctrl']
        + list("asdfghjkl;'`") + ['LShift', '\\'] + list('zxcvbnm,./'))
UKR_LOWER = {'s': 0xF7, ']': 0xF9, "'": 0xF5, '\\': 0xF3, '`': ord("'")}
UKR_UPPER = {'s': 0xF6, ']': 0xF8, "'": 0xF4, '\\': 0xF2}



def glyph(rows):
    """16 rows of '.'/'#' (missing rows at the bottom are blank) -> 16 bytes."""
    rows = rows + ['........'] * (16 - len(rows))
    return bytes(int(r.replace('.', '0').replace('#', '1'), 2) for r in rows)


GHE_UP = glyph(['......##', '......##', '#######.', '.##.....', '.##.....', '.##.....', '.##.....',
                '.##.....', '.##.....', '.##.....', '.##.....', '####....'])
ghe_up = glyph(['........', '........', '........', '......##', '......##', '#######.', '.##.....',
                '.##.....', '.##.....', '.##.....', '.##.....', '####....'])


def build_kbd(src, dst, ukr_tables):
    data = bytearray(open(os.path.join(HERE, src), 'rb').read())
    assert len(data) == 6 * 53, src
    for t, changes in ukr_tables:
        for key, code in changes.items():
            data[t * 53 + KEYS.index(key)] = code
    open(os.path.join(HERE, dst), 'wb').write(data)


def cp1125_glyphs(original, height):
    def g(code):
        return original[code * height:(code + 1) * height]
    if height == 8:
        upper = bytes([0x06, 0x06, 0x7e, 0x60, 0x60, 0x60, 0x60, 0])
        lower = bytes([0, 0x06, 0x06, 0x7e, 0x60, 0x60, 0x60, 0])
    else:
        upper, lower = GHE_UP[:height], ghe_up[:height]
    return {0xF2: upper, 0xF3: lower,
            0xF4: g(0xF2), 0xF5: g(0xF3),
            0xF6: g(0x49), 0xF7: g(0x69),
            0xF8: g(0xF4), 0xF9: g(0xF5)}


def build_fonts(folder):
    """Staged PATCH_FIX1 fonts (unchanged by FIX2-FIX4) -> cp1125 in place, one 'db' line per character."""
    for height in (8, 14, 16):
        name = 'FONT8X%02d.INC' % height
        lines = (Path(folder) / name).read_bytes().split(b'\r\n')
        assert len(lines) == 257 and lines[256] == b''
        rows = [bytes(int(x, 16) for x in re.findall(rb'0([0-9A-F]{2})h', l)) for l in lines[:256]]
        assert all(len(r) == height for r in rows)
        for code, bits in cp1125_glyphs(b''.join(rows), height).items():
            lines[code] = b'db ' + b','.join(b'0%02Xh' % x for x in bits) + b'; %03X' % code
        (Path(folder) / name).write_bytes(b'\r\n'.join(lines))


def build_table():
    lines = ['#    Name:     cp1125 (RUSCII, Ukrainian DOS) to Unicode table',
             '#    For DOSBox-X: [dos] customcodepage=1125,<full path of this file>, then CHCP 1125', '#']
    # 01h-1Fh and 7Fh are the screen glyphs of every DOS code page (☺ • ► ▲ ⌂ ...), not controls:
    # DOSBox-X TrueType output draws them from this table (FoxPro radio buttons, scroll bars, menu arrows)
    glyphs = dict(zip([*range(1, 32), 0x7F], '☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼⌂'))
    for b in range(256):
        ch = glyphs.get(b) or bytes([b]).decode('cp1125')
        name = unicodedata.name(ch, '<control>')
        lines.append('0x%02X\t0x%04X\t#%s' % (b, ord(ch), name))
    with open(os.path.join(HERE, 'CP1125.TXT'), 'w', newline='\r\n') as f:
        f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    build_kbd('UAL.KBD', 'UAL1125.KBD', [(0, UKR_LOWER), (1, UKR_UPPER)])
    build_kbd('URL.KBD', 'URL1125.KBD', [(2, UKR_LOWER), (3, UKR_UPPER)])
    build_table()
    print('done')
