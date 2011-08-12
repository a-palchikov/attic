# /usr/bin/env python

from construct import *

__all__ = ['PrintContext', 'AlignedStruct4', 'merge_subcon', 'aligned4', 'get_parsed_size']

DWORD_ = 4

def get_parsed_size(tp, ctx):
    return len(tp.build(ctx))

class PrintContext(Construct):
    def _parse(self, stream, context):
        print context

def aligned4(size):
    return (size + (DWORD_ - 1)) & (0 - DWORD_)

class AlignedStruct4(Struct):
    def _parse(self, stream, context):
        pos = stream.tell()
        data = Struct._parse(self, stream, context)
        pos_end = stream.tell()
        # ap(todo): how do I compute sizeof(subcon)???
        size = pos_end - pos # Struct._sizeof(self, context)
        aligned_length = aligned4(size)
        if aligned_length > size:
            # ignore the input
            stream.read(aligned_length - size)
        return data

    ## ap(todo) implement building
    ##def _build(self, ...):
    ##    pass

    """
    def _sizeof(self, context):
        pdb.set_trace()
        size = Struct._sizeof(self, context)
        return (size + (AlignedStruct4.DWORD_ - 1)) & (0 - AlignedStruct4.DWORD_)
    """

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

