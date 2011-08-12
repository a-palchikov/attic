from construct import *
from cStringIO import StringIO
from pdbparse.tpi import merge_subcon

symPub = Struct("data_v3",
    ULInt32("symtype"),
    ULInt32("offset"),
    ULInt16("segment"),
    CString("name"),
)

symProc = Struct('procref',
    ULInt32('sumName'),
    ULInt32('ibSym'),
    ULInt16('imod'),
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

sym_id = Enum(ULInt16('sym_id'),
    S_PUB32           = 0x110E,
    S_PROCREF         = 0x1125,
    S_LPROCREF        = 0x1127,
)

gsym = Struct("global",
    #ULInt16("leaf_type"),
    sym_id,
    Switch("data", lambda ctx: ctx.sym_id,
        {
            'S_PUB32': symPub,
            'S_PROCREF': symProc,
            'S_LPROCREF': symProc,   # local proc ref
        },
        default = Pass,
    ),
)

GlobalsData = GreedyRange(
    Tunnel(
        PascalString("globals", length_field=ULInt16("len")),
        gsym,
    )
)

def parse(data):
    con = GlobalsData.parse(data)
    for sc in con:
        merge_subcon(sc, "data")
    return con

def parse_stream(stream):
    con = GlobalsData.parse_stream(stream)
    for sc in con:
        merge_subcon(sc, "data")
    return con
