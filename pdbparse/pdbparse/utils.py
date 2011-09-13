# /usr/bin/env python

from construct import Construct, Struct, Adapter, Anchor, Restream, StringAdapter, Field
from construct.lib import BitStreamReader, BitStreamWriter

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

__all__ = ['PrintContext', 'AlignedStruct4', 'SizedStruct', 'merge_subcon', 'aligned4', 'get_parsed_size', 'StringBuffer', 'HexDumpAdapter']

DWORD_ = 4

#def get_parsed_size(tp, ctx):
#    return len(tp.build(ctx))
#
def get_parsed_size(con):
    return con._end - con._start

class PrintContext(Construct):
    def _parse(self, stream, context):
        print context

def aligned4(size):
    return (size + (DWORD_ - 1)) & (0 - DWORD_)

class AltBitStreamReader(BitStreamReader):
    def close(self):
        # ap(g1001): how do i tell if a specific amount of n-precision bitfields
        # can be represented as m bytes (nopping unused with blanks)
        # example: series of 5 4-bit descriptors, sum up to 20 bits, but are
        # actually represented as 3 bytes (24 bits)
        # i'm going to disable this bloody for now, since it does more harm
        # than it does good
        if (self.total_size + len(self.buffer)) % 8 != 0:
            raise ValueError("total size of read data must be a multiple of 8",
                self.total_size)

# BitStruct that fixes some issues with BitStreamReader
def AltBitStruct(name, *subcons):
    def resizer(length):
        if length & 7:
            raise SizeofError("size must be a multiple of 8", length)
        return length >> 3
    return Restream(Struct(name, *subcons),
            stream_reader = AltBitStreamReader,
            stream_writer = BitStreamWriter,
            resizer = resizer)

class SizedStruct(Struct):
    def __init__(self, name, *subcons, **kw):
        subcons = (Anchor("_start"),) + subcons + (Anchor("_end"),)
        Struct.__init__(self, name, *subcons, **kw)
    def size(self):
        return get_parsed_size(self)

class AlignedStruct4(SizedStruct):
    def _parse(self, stream, context):
        data = Struct._parse(self, stream, context)
        size = data._end - data._start
        aligned_length = aligned4(size)
        if aligned_length > size:
            # ignore the input
            stream.read(aligned_length - size)
        return data

def StringBuffer(name, length, encoding=None):
    """String buffer with known size
    """
    length_fn = callable(length) and length or (lambda ctx: length)
    return StringAdapter(
        Field(name, length_fn),
        encoding=encoding,
    )

def OnDemandString(name):
    return OnDemand(CString(name))

_printable = dict((chr(i), ".") for i in range(256))
_printable.update((chr(i), chr(i)) for i in range(32, 128))
 
def hexdump(data, linesize = 16, showoffset = True, showascii = True):
    prettylines = []
    if showoffset:
        if len(data) < 65536:
            fmt = "%04X   "
        else:
            fmt = "%08X   "
    for i in xrange(0, len(data), linesize):
        line = data[i : i + linesize]
        hextext = " ".join(b.encode("hex") for b in line)
        rawtext = "".join(_printable[b] for b in line)
        result = ""
        if showoffset:
            result += fmt % i
        result += "%-*s" % (3 * linesize - 1, hextext)
        if showascii:
            result += "   %s" % rawtext
        prettylines.append(result)
    return prettylines
 
class HexString(str):
    """Represents a string that will be hex-dumped (only via __pretty_str__).
    this class derives of str, and behaves just like a normal string in all
    other contexts.
    """
    def __init__(self, data, linesize = 16, showoffset = True, showascii = True):
        str.__init__(self, data)
        self.linesize = linesize
        self.showoffset = showoffset
        self.showascii = showascii
    def __new__(cls, data, *args, **kwargs):
        return str.__new__(cls, data)
    def __pretty_str__(self, nesting = 1, indentation = "    "):
        sep = "\n" + indentation * nesting
        return sep + sep.join(hexdump(self, self.linesize, self.showoffset, self.showascii))

class HexDumpAdapter(Adapter):
    """Adapter for hex-dumping strings. It returns a HexString, which is a string
    """
    __slots__ = ["linesize", "showoffset", "showascii"]
    def __init__(self, subcon, linesize = 16, showoffset = True, showascii = True):
        Adapter.__init__(self, subcon)
        self.linesize = linesize
        self.showoffset = showoffset
        self.showascii = showascii
    def _encode(self, obj, context):
        return obj
    def _decode(self, obj, context):
        return HexString(obj, linesize=self.linesize, showoffset=self.showoffset, showascii=self.showascii)

def merge_subcon(parent, subattr):
    """Merge a subcon's fields into its parent.

    parent: the Container into which subattr's fields should be merged
    subattr: the name of the subconstruct
    """

    subcon = getattr(parent, subattr)
    if subcon is None:
        #print 'No %s.%s attribute defined ()' % (repr(parent), subattr)
        pass
    else:
        for a in (k for k in subcon.__attrs__ if not k.startswith("_")):
            setattr(parent, a, getattr(subcon, a))

    delattr(parent, subattr)

