"""
# Serialization and Interpretation checks.
"""
from .. import objects
from .. import types

samples = {
	'v-field': None,
	'b-field': True,
	'i-field': 1234567890,
	's-field': "string data",
	'r-field': 1.2599,
	'o-field': b"octet data",
}

TE1 = types.EStruct.from_fields_v1(
	"http://if.fault.io/test/events",
	symbol="TEST-SIGNAL",
	abstract="ambiguous test event",
	identifier="A",
	code=1,
)

TE2 = types.EStruct.from_fields_v1(
	"http://if.fault.io/test/events",
	symbol="TEST-SIGNAL",
	abstract="ambiguous test event",
	identifier="B",
	code=2,
)

TE3 = types.EStruct.from_fields_v1(
	"http://if.fault.io/test/events",
	symbol="TEST-SIGNAL",
	abstract="ambiguous test event",
	identifier="C",
	code=3,
)

trace = types.Trace.from_events_v1([
	(TE1, types.Parameters.from_pairs_v1({'k':1}.items())),
	(TE2, types.Parameters.from_pairs_v1({'o':b"data"}.items())),
	(TE3, types.Parameters.from_nothing_v1()),
])

roots = [
	types.Failure,
	types.Report,
	types.Message,
]

def test_allocate_sanity(test):
	"""
	# - &objects.allocate
	"""
	stp = objects.allocate()
	test.isinstance(stp, objects.Transport)

def test_Transport_cycle_parameter_samples(test):
	"""
	# - &objects.Transport
	"""
	stp = objects.allocate()
	sequenced = {k:[v] for k,v in samples.items()}
	sets = {k:set([v]) for k,v in samples.items()}

	for sample in [samples, sequenced, sets]:
		p = types.Parameters.from_pairs_v1(sample.items())
		i_p = stp.prepare(p)
		o_p = stp.interpret(i_p)

		test/p == o_p

		# Validate that comparison is sane.
		p.set_parameter('test-failure', 'no-corresponding-value')
		test/p != o_p

def test_Transport_default_roots(test):
	"""
	# - &objects.Transport

	# Check transmission and the recreated equality.
	"""
	import json
	stp = objects.allocate()

	# Trace; usually not root, but transmittable.
	prepared = stp.prepare(trace)
	interpreted = stp.interpret(json.loads(json.dumps(prepared)))
	test/interpreted == trace

	# Roots
	p = types.Parameters.from_nothing_v1()
	for Root in roots:
		ri = Root((TE1, p, trace))
		prepared = stp.prepare(ri)
		interpreted = stp.interpret(json.loads(json.dumps(prepared)))
		test/interpreted == ri
		test/interpreted[0] == TE1

def test_Transport_relation(test):
	"""
	# - &objects.Transport
	"""
	import json
	stp = objects.allocate()

	# Trace; usually not root, but transmittable.
	rel = types.Parameters.from_relation_v1(
		['id', 'name'],
		['integer', 'string'],
		[
			(1, "Name"),
		]
	)

	report = types.Report.from_arguments_v1(trace, TE1, data=rel)

	prepared = stp.prepare(report)
	interpreted = stp.interpret(json.loads(json.dumps(prepared)))
	test/interpreted == report

	reldata = list(interpreted.r_parameters['data'].select(['id', 'name']))
	test/reldata[0] == (1, "Name")
