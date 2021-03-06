#!/usr/bin/env python

from struct import unpack,calcsize
from construct import HexDumpAdapter, String, CString, ListContainer
import os
from pdbparse.utils import StringIO

debug = True
if debug:
    import pdb

PDB_STREAM_ROOT   = 0 # PDB root directory
PDB_STREAM_PDB    = 1 # PDB stream info
PDB_STREAM_TPI    = 2 # type info
PDB_STREAM_DBI    = 3 # debug info

_PDB2_SIGNATURE = "Microsoft C/C++ program database 2.00\r\n\032JG\0\0"
_PDB2_SIGNATURE_LEN = len(_PDB2_SIGNATURE)
_PDB2_FMT = "<%dsLHHLL" % _PDB2_SIGNATURE_LEN
_PDB2_FMT_SIZE = calcsize(_PDB2_FMT)

_PDB7_SIGNATURE = 'Microsoft C/C++ MSF 7.00\r\n\x1ADS\0\0\0'
_PDB7_SIGNATURE_LEN = len(_PDB7_SIGNATURE)
_PDB7_FMT = "<%dsLLLLLL" % _PDB7_SIGNATURE_LEN
_PDB7_FMT_SIZE = calcsize(_PDB7_FMT)

# Internal method to calculate the number of pages required
# to store a stream of size "length", given a page size of
# "pagesize"
def _pages(length, pagesize):
    num_pages = length / pagesize
    if (length % pagesize): num_pages += 1
    return num_pages

class PDataCache:
    def __init__(self, start_page=-1, end_page=-1, data_buffer=None):
        self.pn_start = start_page
        self.pn_end = end_page
        self.buffer = data_buffer
    def __eq__(self, other):
        """
        Compares data cache to a tuple
        Tuple is not type-checked since it's internal use only
        """
        return self.pn_start == other[0] and self.pn_end == other[1]
    def __ne__(self, other):
        return not (self == other)
    def set_cached(self, start, end, buffer):
        self.pn_start = start
        self.pn_end = end
        self.buffer = buffer

class StreamFile:
    def __init__(self, fp, pages, size=-1, page_size=0x1000):
        self.fp = fp
        self.pages = pages
        self.page_size = page_size
        if size == -1: self.end = len(pages)*page_size
        else: self.end = size
        self.pos = 0
        # data cache
        self.pdata = PDataCache()

    def read(self, size=-1):
        if size == -1:
            pn_start, off_start = self._get_page(self.pos)
            pdata = self._read_pages(self.pages[pn_start:])
            self.pos = self.end
            return pdata[off_start:self.end-off_start]
        else:
            if self.pos >= self.end:
                return ''
            pn_start, off_start = self._get_page(self.pos)
            pn_end, off_end = self._get_page(self.pos + size)
            #"""
            if self.pdata == (pn_start, pn_end):
                pdata = self.pdata.buffer
            else:
                pdata = self._read_pages(self.pages[pn_start:pn_end+1])
                self._set_cached(pn_start, pn_end, pdata)
            #"""
            #pdata = self._read_pages(self.pages[pn_start:pn_end+1])

            self.pos += size
            return pdata[off_start:-(self.page_size - off_end)]
    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            self.pos = offset
        elif whence == os.SEEK_CUR:
            self.pos += offset
        elif whence == os.SEEK_END:
            self.pos = self.end + offset
        if self.pos < 0: self.pos = 0
        if self.pos > self.end: self.pos = self.end
    def tell(self):
        return self.pos
    def close(self):
        self.fp.close()
    def _set_cached(self, pn_start, pn_end, buffer):
        self.pdata.set_cached(pn_start, pn_end, buffer)

    # Private helper methods
    def _get_page(self, offset):
        return (offset / self.page_size, offset % self.page_size)
    def _read_pages(self, pages):
        s = []
        for pn in pages:
           self.fp.seek(pn*self.page_size)
           s.append(self.fp.read(self.page_size))
        return ''.join(s)

class PDBStream:
    """Base class for PDB stream types.

    data: the data that makes up this stream
    index: the index of this stream in the file
    page_size: the size of a page, in bytes, of the PDB file
        containing this stream

    The constructor signature here is valid for all subclasses.

    """
    def _get_data(self):
        pos = self.stream_file.tell()
        data = self.stream_file.read()
        self.stream_file.seek(pos)
        return data
    data = property(fget=_get_data)

    def __init__(self, fp, pages, index, size=-1, page_size=0x1000):
        self.pages = pages
        self.index = index
        self.page_size = page_size
        if size == -1: self.size = len(pages)*page_size
        else: self.size = size
        self.stream_file = StreamFile(fp, pages, size=size, page_size=page_size)

    # default load grabs the first page wrapped in HexDumpAdapter
    def load(self):
        self.raw_buffer = HexDumpAdapter(String('Raw_Data', self.page_size)).parse_stream(self.stream_file)

class PDB7RootStream(PDBStream):
    """Class representing the root stream of a PDB file.
    
    Parsed streams are available as a tuple of (size, [list of pages])
    describing each stream in the "streams" member of this class.

    """
    def __init__(self, fp, pages, index=PDB_STREAM_ROOT, size=-1,
            page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index, size=size, page_size=page_size)

        data = self.data
        
        (self.num_streams,) = unpack("<L", data[:4])
        
        # num_streams dwords giving stream sizes
        rs = data[4:]
        sizes = []
        for i in range(0,self.num_streams*4,4):
            (stream_size,) = unpack("<L",rs[i:i+4])
            sizes.append(stream_size)
        
        # Next comes a list of the pages that make up each stream
        rs = rs[self.num_streams*4:]
        page_lists = []
        pos = 0
        for i in range(self.num_streams):
            num_pages = _pages(sizes[i], self.page_size)

            if num_pages != 0:
                pages = unpack("<" + ("%sL" % num_pages),
                               rs[pos:pos+(num_pages*4)])
                page_lists.append(pages)
                pos += num_pages*4
            else:
                page_lists.append(())
        
        self.streams = zip(sizes, page_lists)

class PDB2RootStream(PDBStream):
    """Class representing the root stream of a PDBv2 file.
    
    Parsed streams are available as a tuple of (size, [list of pages])
    describing each stream in the "streams" member of this class.

    """
    def __init__(self, fp, pages, index=PDB_STREAM_ROOT, size=-1,
            page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index, size=size, page_size=page_size)
        data = self.data
        
        (self.num_streams, reserved) = unpack("<HH", data[:4])
        
        # num_streams
        rs = data[4:]
        sizes = []
        for i in range(0,self.num_streams*8,8):
            (stream_size,ptr_reserved) = unpack("<LL",rs[i:i+8])
            sizes.append(stream_size)
        
        # Next comes a list of the pages that make up each stream
        rs = rs[self.num_streams*8:]
        page_lists = []
        pos = 0
        for i in range(self.num_streams):
            num_pages = _pages(sizes[i], self.page_size)

            if num_pages != 0:
                pages = unpack("<" + ("%dH" % num_pages),
                               rs[pos:pos+(num_pages*2)])
                page_lists.append(pages)
                pos += num_pages*2
            else:
                page_lists.append(())
        
        self.streams = zip(sizes, page_lists)

class PDBInfoStream(PDBStream):
    def __init__(self, fp, pages, index=PDB_STREAM_PDB, size=-1,
            page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index, size=size, page_size=page_size)
        self.load()
    def load(self):
        import info
        from datetime import datetime

        inf = info.parse_stream(self.stream_file)
        self.Version = inf.Version
        self.TimeDateStamp = datetime.fromtimestamp(inf.TimeDateStamp)
        self.Age = inf.Age
        self.GUID = inf.GUID
        # build named streams
        self.names = {}
        for i in xrange(inf.NumNames):
            self.names[CString("foo").parse(inf.NameBuffer[inf.NameStreams[i].Offset:])] = inf.NameStreams[i].StreamIndex

        del inf

class PDBTypeStream(PDBStream):
    def __init__(self, fp, pages, index=PDB_STREAM_TPI, size=-1,
            page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index, size=size, page_size=page_size)
    def load(self,unnamed_hack=True,elim_fwdrefs=True):
        import tpi
        tpis = tpi.parse_stream(self.stream_file,unnamed_hack,elim_fwdrefs)
        self.header = tpis.TPIHeader
        self.num_types = self.header.ti_max - self.header.ti_min
        self.types = tpis.types
        self.structures = dict((s.name, s) for s in tpis.types.values()
            if s.leaf_type == "LF_STRUCTURE" or s.leaf_type == "LF_STRUCTURE_ST")
        del tpis

class PDBDebugStream(PDBStream):
    def __init__(self, fp, pages, index=PDB_STREAM_PDB, size=-1,
            page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index, size=size, page_size=page_size)
        self.load()
    def load(self):
        import dbi
        debug = dbi.parse_stream(self.stream_file)

        self.version = debug.DBIHeader.version
        self.pdb_age = debug.DBIHeader.pdb_age
        self.gsi_stream_no = debug.DBIHeader.gsi_stream
        self.psi_stream_no = debug.DBIHeader.psi_stream
        self.sym_stream_no = debug.DBIHeader.sym_stream
        self.module_size = debug.DBIHeader.module_size
        self.offset_size = debug.DBIHeader.offset_size
        self.hash_size = debug.DBIHeader.hash_size
        self.srcmodule_size = debug.DBIHeader.srcmodule_size
        self.pdbimport_size = debug.DBIHeader.pdbimport_size
        self.fpoext_stream_no = debug.StreamIndexesData.FPO_EXT
        self.exhdrs = debug.DBIExHeaders
        
        del debug

class PDBGlobalSymbolStream(PDBStream):
    def __init__(self, fp, pages, index=PDB_STREAM_PDB, size=-1, page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index, size=size, page_size=page_size)
        self.load()
    def load(self):
        import gdata
        self.globals = gdata.parse_stream(self.stream_file)

class PDBPrivateSymbolStream(PDBStream):
    def __init__(self, fp, pages, index, size, page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index, size=size, page_size=page_size)
        self.load()
    def load(self):
        import gdata
        self.globals = gdata.parse_stream(self.stream_file, 4)

class PDBFPOStream(PDBStream):
    def __init__(self, fp, pages, index, size=-1, page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index=index, size=size, page_size=page_size)
        self.load()
    def load(self):
        import fpo
        self.records = fpo.parse_stream(self.stream_file, self.size)

class PDBNamesStream(PDBStream):
    def __init__(self, fp, pages, index, size=-1, page_size=0x1000):
        PDBStream.__init__(self, fp, pages, index=index, size=size, page_size=page_size)
        self.load()
    def load(self):
        import fpo
        self.records = fpo.FPO_STRING_DATA.parse_stream(self.stream_file)

# Class mappings for the stream types
_stream_types7 = {
# Removing this: it's redundant and causing problems
#    PDB_STREAM_ROOT: PDB7RootStream,
    PDB_STREAM_TPI: PDBTypeStream,
    PDB_STREAM_PDB: PDBInfoStream,
    PDB_STREAM_DBI: PDBDebugStream,
}

_stream_types2 = {
    PDB_STREAM_ROOT: PDB2RootStream,
    PDB_STREAM_TPI: PDBTypeStream,
    #PDB_STREAM_PDB: PDBInfoStream,
    PDB_STREAM_DBI: PDBDebugStream,
}

class PDB:
    def __init__(self, fp):
        #self.fp = fp
        import mmap
        self.fp = mmap.mmap(fp.fileno(), 0)

    def read(self, pages, size=-1):
        """Read a portion of this PDB file, given a list of pages.
        
        pages: a list of page numbers that make up the data requested
        size: the number of bytes requested. Must be <= len(pages)*self.page_size
        
        """
        
        assert size <= len(pages)*self.page_size

        pos = self.fp.tell()
        s = []
        for pn in pages:
           self.fp.seek(pn*self.page_size)
           s.append(self.fp.read(self.page_size))
        self.fp.seek(pos)
        s = ''.join(s)
        if size == -1:
            return s
        else:
            return s[:size]

    def read_root(self, rs):
        self.streams = []
        for i in range(len(rs.streams)):
            try:
                pdb_cls = self._stream_map[i]
            except KeyError:
                pdb_cls = PDBStream
            stream_size, stream_pages = rs.streams[i]
            pdb_stream = pdb_cls(self.fp, stream_pages, i, size=stream_size,
                                page_size=self.page_size)
            self.streams.append(pdb_stream)

    def load_type_info(self):
        """Populates type information stream
        """
        self.streams[DPB_STREAM_TPI].load()

    def guid(self):
        """PDB GUID helper
        """
        return self.streams[PDB_STREAM_PDB].GUID

    def age(self):
        """PDB age helper
        """
        return self.streams[PDB_STREAM_PDB].Age

class PDB7(PDB):
    """Class representing a Microsoft PDB file, version 7.

    This class loads and parses each stream contained in the
    file, and places it in the "streams" member.

    """

    def __init__(self, fp):
        PDB.__init__(self, fp)
        (self.signature, self.page_size, alloc_table_ptr,
         self.num_file_pages, root_size, reserved,
         root_index) = unpack(_PDB7_FMT, self.fp.read(_PDB7_FMT_SIZE))
        
        if self.signature != _PDB7_SIGNATURE:
            raise ValueError("Invalid signature for PDB version 7")
        
        self._stream_map = _stream_types7

        # Read in the root stream
        num_root_pages = _pages(root_size, self.page_size)
        
        self.fp.seek(root_index * self.page_size)
        page_list_fmt = "<" + ("%dL" % num_root_pages)
        root_page_list = unpack(page_list_fmt,
            self.fp.read(num_root_pages * 4))
        root_stream_data = self.read(root_page_list, root_size)

        self.root_stream = PDB7RootStream(self.fp, root_page_list,
            index=PDB_STREAM_ROOT, size=root_size, page_size=self.page_size)

        self.read_root(self.root_stream)

        # Load private symbol data
        self.globals = ListContainer()
        if len(self.streams[PDB_STREAM_DBI].exhdrs) > 0:
            for module in self.streams[PDB_STREAM_DBI].exhdrs:
                sno = module.file
                if module.symbol_size > 0:
                    self.streams[sno] = PDBPrivateSymbolStream(self.fp, self.streams[sno].pages,
                        sno, size=module.symbol_size, page_size=self.page_size)
                    self.merge_globals(self.streams[sno].globals)
                    del self.streams[sno].globals

        # Load FPO data if available
        if self.streams[PDB_STREAM_DBI].fpoext_stream_no is not None:
            sno = self.streams[PDB_STREAM_DBI].fpoext_stream_no
            self.streams[sno] = PDBFPOStream(self.fp, self.streams[sno].pages,
                sno, size=self.streams[sno].size, page_size=self.page_size)

        if '/names' in self.streams[PDB_STREAM_PDB].names:
            sno = self.streams[PDB_STREAM_PDB].names['/names']
            self.streams[sno] = PDBNamesStream(self.fp, self.streams[sno].pages,
                sno, size=self.streams[sno].size, page_size=self.page_size)

    def load_public_info(self):
        """
        Loading public symbol information requires explicit call to this method
        Populates global public stream
        """
        # Load global symbols stream, if present
        if self.streams[PDB_STREAM_DBI].sym_stream_no is not None:
            sno = self.streams[PDB_STREAM_DBI].sym_stream_no
            self.streams[sno] = PDBGlobalSymbolStream(self.fp, self.streams[sno].pages,
                sno, size=self.streams[sno].size, page_size=self.page_size)

    def merge_globals(self, globals):
        """
        Merge globals to self.globals
        """
        # ap(todo): filter?..
        self.globals += globals

class PDB2(PDB):
    def __init__(self, fp):
        PDB.__init__(self, fp)
        (self.signature, self.page_size, start_page,
         self.num_file_pages, root_size, reserved) = unpack(_PDB2_FMT, 
                 self.fp.read(_PDB2_FMT_SIZE))
        
        if self.signature != _PDB2_SIGNATURE:
            raise ValueError("Invalid signature for PDB version 2")
        
        self._stream_map = _stream_types2

        # Read in the root stream
        num_root_pages = _pages(root_size, self.page_size)
        
        page_list_fmt = "<" + ("%dH" % num_root_pages)
        root_page_list = unpack(page_list_fmt,
            self.fp.read(num_root_pages * 2))

        self.root_stream = PDB2RootStream(self.fp, root_page_list,
            index=PDB_STREAM_ROOT, page_size=self.page_size)

        self.read_root(self.root_stream)

        # Load global symbols, if present
#        if not fast_load and self.streams[PDB_STREAM_DBI].gsym_file:
#            gsf = self.streams[PDB_STREAM_DBI].gsym_file
#            self.streams[gsf] = PDBGlobalSymbolStream(self.fp, self.streams[gsf].pages,
#                gsf, size=self.streams[gsf].size, page_size=self.page_size,
#
def parse(filename):
    "Open a PDB file and autodetect its version"
    f = open(filename, 'rb')
    sig = f.read(_PDB7_SIGNATURE_LEN)
    f.seek(0)
    if sig == _PDB7_SIGNATURE:
        return PDB7(f)
    else:
        sig = f.read(_PDB2_SIGNATURE_LEN)
        if sig == _PDB2_SIGNATURE:
            f.seek(0)
            return PDB2(f)
    raise ValueError("Unsupported file type")
