from construct import *
from cStringIO import StringIO
from pdbparse.tpi import merge_subcon
from pdbparse.utils import aligned4

symPub = Struct('public_symbol',
    ULInt32('symtype'),
    ULInt32('offset'),
    ULInt16('segment'),
    CString('name'),
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
    CString('name'),
)

symConst = Struct('const',
    ULInt32('type'),
    ULInt16('cvalue'),
    CString('name'),
)

symUdt = Struct('udt',
    ULInt32('type'),
    CString('name'),
)

symThunk = Struct('plt_slot',
    ULInt32('pparent'),
    ULInt32('pend'),
    ULInt32('next'),
    ULInt32('offset'),
    ULInt16('segemnt'),
    ULInt16('length'),
    ULInt8('type'),
    CString('name'),
)

sym_id = Enum(ULInt16('sym_id'),
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
        },
        default = Pass,
        #default = HexDumpAdapter(
        #    Field("data", lambda ctx: ctx._.sizeof-2)
        #),
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

def parse(data):
    return parse_stream(StringIO(data))

def parse_stream(stream):
    con = GlobalsData.parse_stream(stream)
    #import pdb
    #pdb.set_trace()
    for sc in con:
        merge_subcon(sc, 'data')
    return con
