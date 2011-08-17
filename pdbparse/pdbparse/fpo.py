#!/usr/bin/env python

from construct import *
from pdbparse.utils import get_parsed_size

# FPO DATA
FPO_DATA = Struct("FPO_DATA",
    ULInt32("ulOffStart"),          # offset 1st byte of function code
    ULInt32("cbProcSize"),          # number of bytes in function
    ULInt32("cdwLocals"),           # number of bytes in locals/4
    ULInt16("cdwParams"),           # number of bytes in params/4
    BitStruct("BitValues",
        Octet("cbProlog"),          # number of bytes in prolog
        BitField("cbFrame",2),      # frame type
        Bit("reserved"),            # reserved for future use
        Flag("fUseBP"),             # TRUE if EBP has been allocated
        Flag("fHasSEH"),            # TRUE if SEH in func
        BitField("cbRegs",3),       # number of regs saved
    ),
)

FPOFlags = FlagsEnum(ULInt32('FPO_FLAGS'),
    PDB_FPO_NONE          = 0x00000000,
    PDB_FPO_DFL_SEH       = 0x00000001,
    PDB_FPO_DFL_EH        = 0x00000002,
    PDB_FPO_DFL_IN_BLOCK  = 0x00000004,
    #_default_             = Pass,
)

# New style FPO records with program strings
FPO_DATA_V2 = Struct("FPO_DATA_V2",
    Anchor("_start"),
    ULInt32("ulOffStart"),
    ULInt32("cbProcSize"),
    ULInt32("cbLocals"),
    ULInt32("cbParams"),
    ULInt32("cbMaxStack"),        # always 0
    ULInt32("ProgramStringOffset"),
    ULInt16("cbProlog"),
    ULInt16("cbSavedRegs"),
    FPOFlags,
    Anchor("_end"),
)

# Ranges for both types
FPO_DATA_LIST = GreedyRange(FPO_DATA)
FPO_DATA_LIST_V2 = GreedyRange(FPO_DATA_V2)

# Program string storage
# May move this to a new file; in private symbols the values
# include things that are not just FPO related.
FPO_STRING_DATA = Struct("FPO_STRING_DATA",
    Const(Bytes("Signature",4), "\xFE\xEF\xFE\xEF"),
    ULInt32("Unk1"),
    ULInt32("szDataLen"),

    # ap: switched to hex for debugging purposes
    HexDumpAdapter(String("Strings", lambda ctx: ctx.szDataLen)),
    #Rename("StringData",
    #    Tunnel(
    #        String("Strings", lambda ctx: ctx.szDataLen),
    #        GreedyRange(CString("Strings")),
    #    ),
    #),

    ULInt32("lastDwIndex"), # data remaining = (last_dword_index+1)*4
    OnDemand(HexDumpAdapter(String("UnkData", lambda ctx: ((ctx.lastDwIndex+1)*4)))),
    #Terminator,
)

def parse(data, sz):
    return parse_stream(StringIO(data), sz)

def parse_stream(stream, sz):
    record = FPO_DATA_V2.parse_stream(stream)
    record_size = record._end - record._start

    try:
        records = Array(lambda ctx: sz / record_size - 1, FPO_DATA_V2).parse_stream(stream)
    except ArrayError, ex:
        import traceback
        traceback.print_exc()
        #pdb.set_trace()

    return records

    """
        Tunnel(
            String('FPO_RECORDS', lambda ctx: sz / record_size),
            GreedyRange(FPO_DATA_V2),
        ).parse_stream(stream)
    """
