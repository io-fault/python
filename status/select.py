"""
# Query interface for status frames.
# Currently, only channel filtering is supported and the command interface is subject to change.
"""
import sys
import os
import typing

from fault.system import files
from fault.system import process
from fault.context import tools
from .. import frames

def main(inv:process.Invocation) -> process.Exit:
	fchannel, *quals = inv.argv
	unpack, pack = frames.stdio()

	for line in sys.stdin.readlines():
		msg = unpack(line)
		channel = msg.f_channel
		if channel is not None and channel.startswith(fchannel):
			sys.stdout.write(line)

	return inv.exit(0)
