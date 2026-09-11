from ...system import files
from ...system import execution as module
from .tools import perform_cat

def test_PInvocation(test):
	data = b"data sent through a cat pipeline\n"
	for count in range(0, 16):
		s = module.PInvocation.from_commands(
			*([('/bin/cat', 'cat')] * count)
		)
		pl = s()
		out, status = perform_cat(pl.process_identifiers, pl.input, pl.output, data, *pl.standard_errors.values())
		test/out == data
		test/len(status) == count
