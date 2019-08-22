#!/usr/bin/env python3
#
# Copyright (c) 2018 Matthew Earl
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
# 
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
#     NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#     DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#     OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#     USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
Super Mario Bros level extractor
This script requires py65emu, numpy, and PIL to run.  Run with no arguments to see usage.
See http://matthewearl.github.io/2018/06/28/smb-level-extractor/ for a description of how this was written.
To run you'll need to compile https://gist.github.com/1wErt3r/4048722 with x816 to obtain the PRG-ROM and symbol files.
The CHR-ROM should be extracted from a Super Mario Bros ROM, or can be read from an INES ROM file.  See
https://wiki.nesdev.com/w/index.php/INES for information on the INES format.  In addition you'll need a NES palette
saved in "data/ntscpalette.pal", generated using the tool here: https://bisqwit.iki.fi/utils/nespalette.php
"""


import collections
import pathlib
import re

import numpy as np

from py65emuLib.py65emu.cpu import CPU
from py65emuLib.py65emu.mmu import MMU


_WORKING_RAM_SIZE = 0x800


Symbol = collections.namedtuple('Symbol', ('name', 'address', 'line_num'))


class SymbolFile:
    _LINE_RE = r"(?P<name>[A-Z0-9_]+) *= \$(?P<address>[A-F0-9]*) *; <> \d+, statement #(?P<line_num>\d+)"
    def __init__(self, fname):
        with open(fname) as f:
            self._symbols = [self._parse_symbol(line) for line in f.readlines()]

        self._symbols = list(sorted(self._symbols, key=lambda s: s.address))
        self._name_to_addr = {s.name: s.address for s in self._symbols}
        self._addr_to_name = {s.address: s.name for s in self._symbols}

    def _parse_symbol(self, line):
        m = re.match(self._LINE_RE, line)
        return Symbol(m.group('name'), int(m.group('address'), 16), int(m.group('line_num')))

    def __getitem__(self, name):
        return self._name_to_addr[name]


def _read_ppu_data(mmu, addr):
    while True:
        ppu_high_addr = mmu.read(addr)
        if ppu_high_addr == 0x0:
            break
        ppu_low_addr = mmu.read(addr + 1)
        assert ppu_high_addr == 0x3f and ppu_low_addr == 0x00
        flags_and_length = mmu.read(addr + 2)
        assert (flags_and_length & (1<<7)) == 0, "32-byte increment flag set"
        assert (flags_and_length & (1<<6)) == 0, "Repeating flag set"
        length = flags_and_length & 0b111111

        addr += 3
        for i in range(length):
            yield mmu.read(addr)
            addr += 1


def _load_palette(mmu, sym_file, nes_palette):
    area_type = mmu.read(sym_file['AREATYPE'])
    idx = mmu.read(sym_file['AREAPALETTE'] + area_type)

    high_addr = mmu.read(sym_file['VRAM_ADDRTABLE_HIGH'] + idx)
    low_addr = mmu.read(sym_file['VRAM_ADDRTABLE_LOW'] + idx)

    palette_data = list(_read_ppu_data(mmu, high_addr << 8 | low_addr))
    assert len(palette_data) == 32

    a = np.array(palette_data[:16]).reshape(4, 4)
    a[:, 0] = mmu.read(sym_file['BACKGROUNDCOLORS'] + area_type)
    
    return nes_palette[a]


def _execute_subroutine(cpu, addr):
    s_before = cpu.r.s
    cpu.JSR(addr)
    while cpu.r.s != s_before:
        cpu.step()


def _get_metatile_buffer(mmu, sym_file):
    return [mmu.read(sym_file['METATILEBUFFER'] + i) for i in range(13)]


def load_tile(chr_rom, idx):
    chr_rom_addr = 0x1000 + 16 * idx
    d = chr_rom[chr_rom_addr:chr_rom_addr + 16]
    a = np.array([[b & (128 >> i) != 0 for i in range(8)] for b in d]).reshape(2, 8, 8)
    return a[0] + 2 * a[1]


def _render_metatile(mmu, chr_rom, mtile, palette):
    palette_num = mtile >> 6
    palette_idx = mtile & 0b111111

    high_addr = mmu.read(sym_file['METATILEGRAPHICS_HIGH'] + palette_num)
    low_addr = mmu.read(sym_file['METATILEGRAPHICS_LOW'] + palette_num)

    addr = (high_addr << 8 | low_addr) + palette_idx * 4

    t = np.vstack([np.hstack([load_tile(chr_rom, mmu.read(addr + c * 2 + r)) for c in range(2)])
                        for r in range(2)])

    return palette[palette_num][t]


def load_level(stage, prg_rom, chr_rom, sym_file, nes_palette):
    # Initialize the MMU / CPU
    mmu = MMU([
            (0x0, _WORKING_RAM_SIZE, False, []),
            (0x8000, 0x10000, True, list(prg_rom))
    ])
    cpu = CPU(mmu, 0x0)

    # Execute some preamble subroutines which set up variables used by the main subroutines.
    if isinstance(stage, tuple):
        world_num, area_num = stage
        mmu.write(sym_file['WORLDNUMBER'], world_num - 1)
        mmu.write(sym_file['AREANUMBER'], area_num - 1)
        _execute_subroutine(cpu, sym_file['LOADAREAPOINTER'])
    else:
        area_pointer = stage
        mmu.write(sym_file['AREAPOINTER'], area_pointer)

    mmu.write(sym_file['HALFWAYPAGE'], 0)
    mmu.write(sym_file['ALTENTRANCECONTROL'], 0)
    mmu.write(sym_file['PRIMARYHARDMODE'], 0)
    mmu.write(sym_file['OPERMODE_TASK'], 0)
    _execute_subroutine(cpu, sym_file['INITIALIZEAREA'])

    # Extract the palette.
    palette = _load_palette(mmu, sym_file, nes_palette)

    # Repeatedly extract meta-tile columns, until the level starts repeating.
    cols = []
    for column_pos in range(1000):
        _execute_subroutine(cpu, sym_file['AREAPARSERCORE'])
        cols.append(_get_metatile_buffer(mmu, sym_file))
        _execute_subroutine(cpu, sym_file['INCREMENTCOLUMNPOS'])

        if len(cols) >= 96 and cols[-48:] == cols[-96:-48]:
            cols = cols[:-80]
            break
    level = np.array(cols).T

    # Render a dict of metatiles.
    mtiles = {mtile: _render_metatile(mmu, chr_rom, mtile, palette)
                for mtile in set(level.flatten())}

    return level, mtiles


def render_level(level, mtiles):
    return np.vstack([np.hstack([mtiles[mtile] for mtile in row]) for row in level])


if __name__ == "__main__":
    import sys

    import PIL.Image

    world_map = {
        '{}-{}'.format(world_num, area_num): (world_num, area_num)
            for world_num in range(1, 9)
            for area_num in range(1, 5)
    }
    world_map.update({
        'bonus': 0xc2,
        'cloud1': 0x2b,
        'cloud2': 0x34,
        'water1': 0x00,
        'water2': 0x02,
        'warp': 0x2f,
    })

    if len(sys.argv) < 6:
        print("Usage: {} <world> <prg-rom> <sym-file> <chr-rom> <out-file>".format(sys.argv[0]), file=sys.stderr)
        print("  <world> is one of {}".format(', '.join(sorted(world_map.keys()))), file=sys.stderr)
        print("  <prg-rom> is the binary output from x816")
        print("  <sym-file> is the sym file output from x816")
        print("  <chr-rom> is a CHR-ROM dump")
        print("  <out-file> is the output image name")
        sys.exit(-1)

    stage = world_map[sys.argv[1]]
    with open(sys.argv[2], 'rb') as f:
        prg_rom = f.read()
    sym_file = SymbolFile(sys.argv[3])
    with open(sys.argv[4], 'rb') as f:
        chr_rom = f.read()
    out_fname = sys.argv[5]

    with (pathlib.Path(sys.argv[0]).parent / "data" / "ntscpalette.pal").open("rb") as f:
        nes_palette = np.array(list(f.read())).reshape(64, 3)

    level, mtiles = load_level(stage, prg_rom, chr_rom, sym_file, nes_palette)
    a = render_level(level, mtiles).astype(np.uint8)
    im = PIL.Image.fromarray(a)
    im.save(out_fname)
