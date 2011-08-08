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

gsym = Struct("global",
    ULInt16("leaf_type"),
    Switch("data", lambda ctx: ctx.leaf_type,
        {
            0x110E : symPub,
            0x1125 : symProc,
            0x1127 : symProc,   # local proc ref
            #0x1107 : symConst,
            #0x1108 : symUdt,   # user-defined type
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
