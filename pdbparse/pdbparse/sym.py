
from construct import *
from utils import AlignedStruct4, merge_subcon

symLData = Struct('ldata',
    ULInt32('sym_type'),
    ULInt32('RVA'),
    ULInt16('segment'),
    CString('name'),
)

symThunk = Struct('thunk',
    ULInt32('parent'),
    ULInt32('end'),
    ULInt32('next'),
    ULInt32('RVA'),
    ULInt16('segment'),
    ULInt16('length'),
    ULInt8('type'),
    CString('name'),
)

symProc = Struct('proc',
    ULInt32('parent'),
    ULInt32('end'),
    ULInt32('next'),
    ULInt32('length'),
    ULInt32('debug_start'),
    ULInt32('debug_end'),
    ULInt32('type'),
    ULInt32('RVA'),
    ULInt16('segment'),
    ULInt8('flags'),        # use Flags here?
    CString('name'),
)

symPublic = Struct('public',
    ULInt32('type'),
    ULInt32('RVA'),
    ULInt16('segment'),
    CString('name'),
)

symStack = Struct('stack',
    SLInt32('RVA'),      # Offset relative to BP
    ULInt32('type'),
    CString('name'),
)

symRegRel = Struct('regrel',
    SLInt32('RVA'),      # Offset relative to BP
    ULInt32('type'),
    ULInt16('reg'),
    CString('name'),
)

symReg = Struct('reg',
    ULInt32('type'),
    ULInt16('reg'),
    CString('name'),
)

symBlock = Struct('block',
    ULInt32('parent'),
    ULInt32('end'),
    ULInt32('length'),
    ULInt32('RVA'),
    ULInt16('segment'),
    CString('name'),
)

symLabel = Struct('label',
    ULInt32('RVA'),
    ULInt16('segment'),
    ULInt8('flags'),        # use Flags here?
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

symCompiland = Struct('compiland',
    ULInt32('unknown'),
    CString('name'),
)

symThread = Struct('thread',
    ULInt32('type'),
    ULInt32('RVA'),
    ULInt16('segment'),
    CString('name'),
)

## ?? ssearch

symSecurityCookie = Struct('cookie',
    ULInt32('RVA'),
    ULInt32('unknown'),
)

symFrameInfo = Struct('frame_info',
    ULInt32('size_frame'),
    ULInt32('unknown2'),
    ULInt32('unknown3'),
    ULInt32('size_saved_regs'),
    ULInt32('unknown'),
    ULInt32('eh_RVA'),          # exception handler offset
    ULInt16('eh_section'),      # exception handler section
    ULInt32('flags'),
)

symGData = Rename("symGData", symLData)

# Enum for symbols
sym_id = Enum(ULInt16('sym_id'),
    """
    S_COMPILAND_V1    = 0x0001,
    S_REGISTER_V1     = 0x0002,
    S_CONSTANT_V1     = 0x0003,
    S_UDT_V1          = 0x0004,
    S_SSEARCH_V1      = 0x0005,
    S_END_V1          = 0x0006,
    S_SKIP_V1         = 0x0007,
    S_CVRESERVE_V1    = 0x0008,
    S_OBJNAME_V1      = 0x0009,
    S_ENDARG_V1       = 0x000a,
    S_COBOLUDT_V1     = 0x000b,
    S_MANYREG_V1      = 0x000c,
    S_RETURN_V1       = 0x000d,
    S_ENTRYTHIS_V1    = 0x000e,
    S_BPREL_V1        = 0x0200,
    S_LDATA_V1        = 0x0201,
    S_GDATA_V1        = 0x0202,
    S_PUB_V1          = 0x0203,
    S_LPROC_V1        = 0x0204,
    S_GPROC_V1        = 0x0205,
    S_THUNK_V1        = 0x0206,
    S_BLOCK_V1        = 0x0207,
    S_WITH_V1         = 0x0208,
    S_LABEL_V1        = 0x0209,
    S_CEXMODEL_V1     = 0x020a,
    S_VFTPATH_V1      = 0x020b,
    S_REGREL_V1       = 0x020c,
    S_LTHREAD_V1      = 0x020d,
    S_GTHREAD_V1      = 0x020e,
    S_PROCREF_V1      = 0x0400,
    S_DATAREF_V1      = 0x0401,
    S_ALIGN_V1        = 0x0402,
    S_LPROCREF_V1     = 0x0403,
    """

    S_BPREL16         = 0x0100,
    S_LDATA16         = 0x0101,
    S_GDATA16         = 0x0102,
    S_PUB16           = 0x0103,
    S_LPROC16         = 0x0104,
    S_GPROC16         = 0x0105,
    S_THUNK16         = 0x0106,
    S_BLOCK16         = 0x0107,
    S_WITH16          = 0x0108,
    S_LABEL16         = 0x0109,
    S_CEXMODEL16      = 0x010A,
    S_VFTABLE16       = 0x010B,
    S_REGREL16        = 0x010C,

    S_BPREL32_16t     = 0x0200,
    S_LDATA32_16t     = 0x0201,
    S_GDATA32_16t     = 0x0202,
    S_PUB32_16t       = 0x0203,
    S_LPROC32_16t     = 0x0204,
    S_GPROC32_16t     = 0x0205,
    S_THUNK32_ST      = 0x0206,
    S_BLOCK32_ST      = 0x0207,
    S_WITH32_ST       = 0x0208,
    S_LABEL32_ST      = 0x0209,
    S_CEXMODEL32      = 0x020A,
    S_VFTABLE32_16t   = 0x020B,
    S_REGREL32_16t    = 0x020C,
    S_LTHREAD32_16t   = 0x020D,
    S_GTHREAD32_16t   = 0x020E,
    S_SLINK32         = 0x020F,

    S_LPROCMIPS_16t   = 0x0300,
    S_GPROCMIPS_16t   = 0x0301,

    S_PROCREF_ST      = 0x0400,
    S_DATAREF_ST      = 0x0401,
    S_ALIGN           = 0x0402,
    S_LPROCREF_ST     = 0x0403,
    S_OEM             = 0x0404,

    S_TI16_MAX        = 0x1000,
    S_REGISTER_ST     = 0x1001,
    S_CONSTANT_ST     = 0x1002,
    S_UDT_ST          = 0x1003,
    S_COBOLUDT_ST     = 0x1004,
    S_MANYREG_ST      = 0x1005,
    S_BPREL32_ST      = 0x1006,
    S_LDATA32_ST      = 0x1007,
    S_GDATA32_ST      = 0x1008,
    S_PUB32_ST        = 0x1009,
    S_LPROC32_ST      = 0x100a,
    S_GPROC32_ST      = 0x100b,
    S_VFTTABLE32      = 0x100c,
    S_REGREL32_ST     = 0x100d,
    S_LTHREAD32_ST    = 0x100e,
    S_GTHREAD32_ST    = 0x100f,
    S_LPROCMIPS_ST    = 0x1010,
    S_GPROCMIPS_ST    = 0x1011,
    S_FRAMEPROC       = 0x1012,

    S_COMPILAND32_ST  = 0x1013,
    S_MANYREG2_ST     = 0x1014,
    S_LPROCIA64_ST    = 0x1015,
    S_GPROCIA64_ST    = 0x1016,
    S_LOCALSLOT_ST    = 0x1017,
    S_PARAMSLOT_ST    = 0x1018,
    S_ANNOTATION      = 0x1019,
    S_GMANPROC_ST     = 0x101A,
    S_LMANPROC_ST     = 0x101B,
    S_RESERVED1       = 0x101C,
    S_RESERVED2       = 0x101D,
    S_RESERVED3       = 0x101E,
    S_RESERVED4       = 0x101F,
    S_LMANDATA_ST     = 0x1020,
    S_GMANDATA_ST     = 0x1021,
    S_MANFRAMEREL_ST  = 0x1022,
    S_MANREGISTER_ST  = 0x1023,
    S_MANSLOT_ST      = 0x1024,
    S_MANMANYREG_ST   = 0x1025,
    S_MANREGREL_ST    = 0x1026,
    S_MANMANYREG2_ST  = 0x1027,
    S_MANTYPREF       = 0x1028,
    S_UNAMESPACE_ST   = 0x1029,

    S_END             = 0x0006,     # end of block/function
    S_ST_MAX          = 0x1100,
    S_OBJNAME         = 0x1101,
    S_THUNK32         = 0x1102,
    S_BLOCK32         = 0x1103,     # part of a function (non-contiguous function)
    S_WITH32          = 0x1104,
    S_LABEL32         = 0x1105,
    S_REGISTER        = 0x1106,     # function parameters and locals
    S_CONSTANT        = 0x1107,
    S_UDT             = 0x1108,
    S_COBOLUDT        = 0x1109,
    S_MANYREG         = 0x110A,
    S_BPREL32         = 0x110B,     # function parameters and locals
    S_LDATA32         = 0x110C,     # global and local data symbols
    S_GDATA32         = 0x110D,
    S_PUB32           = 0x110E,
    S_LPROC32         = 0x110F,
    S_GPROC32         = 0x1110,
    S_REGREL32        = 0x1111,     # function parameters and locals
    S_LTHREAD32       = 0x1112,     # variables with thread-local storage
    S_GTHREAD32       = 0x1113,
    S_LPROCMIPS       = 0x1114,
    S_GPROCMIPS       = 0x1115,
    S_COMPILE2        = 0x1116,
    S_MANYREG2        = 0x1117,
    S_LPROCIA64       = 0x1118,
    S_GPROCIA64       = 0x1119,
    S_LOCALSLOT       = 0x111A,
    S_SLOT            = 0x111A,
    S_PARAMSLOT       = 0x111B,
    S_LMANDATA        = 0x111C,
    S_GMANDATA        = 0x111D,
    S_MANFRAMEREL     = 0x111E,
    S_MANREGISTER     = 0x111F,
    S_MANSLOT         = 0x1120,
    S_MANMANYREG      = 0x1121,
    S_MANREGREL       = 0x1122,
    S_MANMANYREG2     = 0x1123,
    S_UNAMESPACE      = 0x1124,
    S_PROCREF         = 0x1125,
    S_DATAREF         = 0x1126,
    S_LPROCREF        = 0x1127,
    S_ANNOTATIONREF   = 0x1128,
    S_TOKENREF        = 0x1129,
    S_GMANPROC        = 0x112A,
    S_LMANPROC        = 0x112B,
    S_TRAMPOLINE      = 0x112C,
    S_MANCONSTANT     = 0x112D,
    S_RECTYPE_LAST    = 0x112D,
    S_RECTYPE_MAX     = 0x112E,
    S_SECTINFO        = 0x1136,
    S_SUBSECTINFO     = 0x1137
    S_ENTRYPOINT      = 0x1138,
    S_SECUCOOKIE      = 0x113A,
    S_MSTOOLINFO      = 0x113C,
    S_MSTOOLENV       = 0x113D,
    _default_         = Pass,
)

symInfo = AlignedStruct4('sym_info',
    sym_id,
    Switch('symbol_type', lambda ctx: ctx.sym_id,
        {
            'S_LDATA32': symLData,
            'S_GDATA32': symGData,
            'S_THUNK32': symThunk,
            'S_BLOCK32': symBlock,
            'S_LABEL32': symLabel,
            'S_REGISTER': symRegister,
            'S_CONSTANT': symConst,
            'S_UDT': symUdt,
            'S_BPREL32': symRegRel,
            'S_PUB': symPublic,
            'S_LPROC32': symProc,
            'S_GPROC32': symProc,
            'S_REGREL32': symRegRel,
            'S_LTHREAD32': symThread,
            'S_GTHREAD32': symThread,
            'S_SECUCOOKIE': symSecurityCookie,
            'S_OBJNAME': symCompiland,
        },
        default = Pass,
        #default = HexDumpAdapter(
        #    Field('data', lambda ctx: ctx._.length - 2)
        #),
    ),
)

# symbols
# ap(todo) (duplicate Structs ok?)
Symbols = Debugger(Struct('symbols',
    SLInt16('length'),
    Tunnel(
        MetaField('sym_info', lambda ctx: ctx.length),
        symInfo
    ),
))

