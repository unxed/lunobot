#!/usr/bin/env python3
# Moved to tools/janitor.py (unxed/lunobot#247, 21-10-2026). This copy in the root only forwards to it, for the sessions
# that read the instruction before the move and for the copies of runners/*.sh on the nodes; it is removed only by the
# owner's decision, once the copies of the runners are updated on all nodes. Call tools/janitor.py.
import os, runpy, sys
_tools = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
sys.stderr.write("janitor.py: moved to tools/janitor.py: call it there (re-read LUNOBOT.md)\n")
sys.path.insert(0, _tools)
sys.argv[0] = os.path.join(_tools, "janitor.py")
runpy.run_path(sys.argv[0], run_name="__main__")
