#!/usr/bin/env python

import pdbparse
import sys

debug = False
if debug:
	import rpdb2; rpdb2.start_embedded_debugger_interactive_password()

pdb = pdbparse.PDB7(open(sys.argv[1], 'rb'))
print len(pdb.streams[2].data)
