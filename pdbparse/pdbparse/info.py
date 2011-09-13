#!/usr/bin/env python

from construct import *
from pdbparse.utils import PrintContext, StringIO

_strarray = GreedyRange(CString("names"))

class StringArrayAdapter(Adapter):
    def _encode(self, obj, context):
        return _strarray._build(StringIO(obj), context)
    def _decode(self, obj, context):
        return _strarray._parse(StringIO(obj), context)

def GUID(name):
    return Struct(name,
        ULInt32("Data1"),
        ULInt16("Data2"),
        ULInt16("Data3"),
        String("Data4", 8),
    )

Info = Struct("Info",
    ULInt32("Version"),
    ULInt32("TimeDateStamp"),
    ULInt32("Age"),
    GUID("GUID"),
    ULInt32("cbNames"),
    #StringArrayAdapter(MetaField("names", lambda ctx: ctx.cbNames)),
    MetaField("NameBuffer", lambda ctx: ctx.cbNames),
    ULInt32("NumNames"),    # count of strings in names
    ULInt32("Unk1"),        # named stream index bitfield
    ULInt32("Unk2"),        # offset to stream index data (offset + 1)
    ULInt32("IndexesMask"), # bit mask of stream indexes
    ULInt32("Unk3"),
    Rename("NameStreams",
        Array(lambda ctx: ctx.NumNames, Struct('NameStream',
            ULInt32("Offset"),     # offset in NameBuffer
            ULInt32("StreamIndex"),
        )),
    ),
)

def parse_stream(stream):
    return Info.parse_stream(stream)

def parse(data):
    return parse(StringIO(data))

