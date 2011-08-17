# /usr/bin/env python

from construct import *
from construct.lib import BitStreamReader, BitStreamWriter

__all__ = ['PrintContext', 'AlignedStruct4', 'SizedStruct', 'merge_subcon', 'aligned4', 'get_parsed_size']

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

class AlignedStruct4(SizedStruct):
    def _parse(self, stream, context):
        data = Struct._parse(self, stream, context)
        size = data._end - data._start
        aligned_length = aligned4(size)
        if aligned_length > size:
            # ignore the input
            stream.read(aligned_length - size)
        return data

def merge_subcon(parent, subattr):
    """Merge a subcon's fields into its parent.

    parent: the Container into which subattr's fields should be merged
    subattr: the name of the subconstruct
    """

    subcon = getattr(parent, subattr)
    # ap ** subcon is None (or how can this be?..) **
    if subcon is None:
        #print 'No %s.%s attribute defined ()' % (repr(parent), subattr)
        pass
    else:
        for a in (k for k in subcon.__attrs__ if not k.startswith("_")):
            setattr(parent, a, getattr(subcon, a))

    delattr(parent, subattr)

