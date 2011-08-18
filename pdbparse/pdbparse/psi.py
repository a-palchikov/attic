
from construct import *

PSI_old = Struct('stream_indexes',
    ULInt16('FPO'),
    ULInt16('unk0'),
    ULInt16('unk1'),
    ULInt16('unk2'),
    ULInt16('unk3'),
    ULInt16('segments'),
)

PSI = Struct('stream_indexes',
    ULInt16('FPO'),
    ULInt16('unk0'),
    ULInt16('unk1'),
    ULInt16('unk2'),
    ULInt16('unk3'),
    ULInt16('segments'),
    ULInt16('unk4'),
    ULInt16('unk5'),
    ULInt16('unk6'),
    ULInt16('FPO_EXT'),
    ULInt16('unk7'),
)

def parse(data):
    return PSI.parse(data)

def parse_stream(data):
    return PSI.parse_stream(data)
