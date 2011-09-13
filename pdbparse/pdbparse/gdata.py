# /usr/bin/env python

from construct import *
from pdbparse.tpi import merge_subcon
from pdbparse.utils import aligned4, StringBuffer, StringIO

symPub = Struct('public_symbol',
    ULInt32('symtype'),
    ULInt32('offset'),
    ULInt16('segment'),
    Anchor('_end'),
    StringBuffer('name', lambda ctx: ctx._._.sizeof - ctx._end),
)

symProc = Struct('method',
    ULInt32('pparent'),
    ULInt32('pend'),
    ULInt32('next'),
    ULInt32('length'),
    ULInt32('debug_start'),
    ULInt32('debug_end'),
    ULInt32('type'),
    ULInt32('offset'),
    ULInt16('segment'),
    ULInt8('flags'),
    Anchor('_end'),
    StringBuffer('name', lambda ctx: ctx._._.sizeof - ctx._end),
)

symConst = Struct('const',
    ULInt32('type'),
    ULInt16('cvalue'),
    Anchor('_end'),
    StringBuffer('name', lambda ctx: ctx._._.sizeof - ctx._end),
)

symUdt = Struct('udt',
    ULInt32('type'),
    Anchor('_end'),
    StringBuffer('name', lambda ctx: ctx._._.sizeof - ctx._end),
)

symThunk = Struct('plt_slot',
    ULInt32('pparent'),
    ULInt32('pend'),
    ULInt32('next'),
    ULInt32('offset'),
    ULInt16('segemnt'),
    ULInt16('length'),
    ULInt8('type'),
    Anchor('_end'),
    StringBuffer('name', lambda ctx: ctx._._.sizeof - ctx._end),
)

sym_id = Enum(ULInt16('sym_id'),
    S_UDT             = 0x1108,
    # public symbols (functions and global variables specified as extern)
    S_PUB32           = 0x110E,
    # global and static functions
    S_LPROC32         = 0x110F,
    S_GPROC32         = 0x1110,
    S_PROCREF         = 0x1125,
    S_LPROCREF        = 0x1127,
    _default_         = Pass,
)

gsym = Struct("global",
    sym_id,
    Switch("data", lambda ctx: ctx.sym_id,
        {
            'S_PUB32': symPub,          # public symbols
            'S_GPROC32': symProc,       # global/local methods/functions
            'S_LPROC32': symProc,
            #'S_UDT': symUdt,
        },
        default = Pass,
    ),
)

"""
GlobalsData = GreedyRange(
    Tunnel(
        PascalString('globals', length_field=ULInt16('len')),
        gsym,
    )
)
"""
GlobalsData = GreedyRange(Struct("globals",
    ULInt16("length"),
    Value("sizeof", lambda ctx: ctx.length > 0 and aligned4(ctx.length)-2 or 0),
    Tunnel(
        Field('globals', lambda ctx: ctx.sizeof),
        gsym,
    ),
))

def parse(data, offset=0):
    return parse_stream(StringIO(data), offset)

def parse_stream(stream, offset=0):
    if offset > 0:
        stream.seek(offset, 1)
    con = GlobalsData.parse_stream(stream)
    for sc in con:
        merge_subcon(sc, 'globals')
    return con
