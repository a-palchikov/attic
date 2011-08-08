
from minidump import *

if __name__ == '__main__':
    import sys
    md = MINIDUMP_HEADER.parse_stream(open(sys.argv[1], 'rb'))
    excr = None
    threads = None
    for stream in range(0, md.NumberOfStreams-1):
        if md.MINIDUMP_DIRECTORY[stream].StreamType == 'ExceptionStream':
            excr = md.MINIDUMP_DIRECTORY[stream]
            if threads is not None:
                break
        if md.MINIDUMP_DIRECTORY[stream].StreamType == 'ThreadListStream':
            threads = md.MINIDUMP_DIRECTORY[stream]
            if excr is not None:
                break

    if excr is not None:
        ethid = excr.DirectoryData.ThreadId
        print 'Exception in thread %ld' % ethid
        for thread in range(0, threads.DirectoryData.NumberOfThreads-1):
            if threads.DirectoryData.MINIDUMP_THREAD[thread].ThreadId == ethid:
                ethread = threads.DirectoryData.MINIDUMP_THREAD[thread]
                print 'Exception context: RVA(%ld), Size(%ld)' % \
                (ethread.ThreadContext.RVA, ethread.ThreadContext.DataSize)
