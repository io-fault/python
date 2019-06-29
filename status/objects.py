"""
# Object-based transport support for &.types I/O.

# Provides a &Transport class mapping &.types instances to primitives according to
# a given configuration. The &allocate function creates a &Transport instance
# consistent with JSON's native types allowing a simple composition to be
# created for the serialization and the parsing of extended status information.

# The functionality of this module is an intermediate layer for use with data
# transports such as JSON. Use of Python's &pickle serialization should not require the
# use of this module unless it is desired to allow customized interpretations
# by the receiver.
"""
import typing
from . import types
from . import core

# This intends to align with JSON making the default
# &Transport instance (&allocate) prepare status that can be directly
# serialized using &json.dumps and read with &json.loads.
default_transport_types = {
	'void',
	'string',
	'identifier',
	'resource-indicator',

	'boolean',
	'integer',
	'rational',
}

def isolate(parameters):
	# Isolate the parameters into distinct sequences encoding the
	# typeform using &core.forms and &core.types character codes.
	types = []
	forms = []
	keys = []
	values = []

	add_type = types.append
	add_form = forms.append
	add_key = keys.append
	add_rvalue = values.append

	# Convert unsupported value intances to representation forms.
	for form, typ, key, value in parameters:
		add_type(typ)
		add_form(form)
		add_key(key)
		add_rvalue(value)

	types = "".join(core.types[x] for x in types)
	forms = "".join(core.forms[x] for x in forms)

	return (forms, types, keys, values)

def integrate(frame,
		typcodes={x:y for y,x in core.types.items()},
		formcodes={x:y for y,x in core.forms.items()},
	):
	# Combine isolated parameters into tuples with decoded typeforms that
	# can be directly loaded into a &types.Parameters instance.
	for form, typ, key, value in zip(*frame):
		yield (formcodes[form], typcodes[typ], key, value)

recursive_types = {
	types.Message: 'message',
	types.Failure: 'failure',
	types.Report: 'report',
	types.Trace: 'trace',
	types.Parameters: 'parameters',
}

class Transport(object):
	"""
	# Parameter set for preparation and interpretation of &.types instances
	# for transport I/O. Essentially, identifies types native to a transport
	# layer and any transformation functions necessary for the exceptions.
	"""

	_transport_transparent = {
		'reference',
		'representation',
		'r-set',
		'r-sequence',
	}

	def __init__(self, tltypes:set):
		self._transport_local = tltypes

	def encode_event(self, estruct):
		# Expecting outer layer to interpret tuples as sequences.
		return estruct

	def encode_report(self, report):
		params = self.encode_parameters(report.r_parameters)
		trace = self.encode_trace(report.r_context)
		return [report.r_event, params, trace]

	def encode_message(self, message):
		params = self.encode_parameters(message.msg_parameters)
		trace = self.encode_trace(message.msg_context)
		return [message.msg_event, params, trace]

	def encode_failure(self, failure):
		params = self.encode_parameters(failure.f_parameters)
		trace = self.encode_trace(failure.f_context)
		return [failure.f_error, params, trace]

	def encode_trace(self, trace):
		tparams = [self.encode_parameters(x[1]) for x in trace.t_route]
		tevents = [x[0] for x in trace.t_route]
		return [tevents, tparams]

	def encode_parameters_internal(self, parameters, rio=core.representation_io):
		for form, stype, key, param in parameters:
			if stype == 'excluded':
				continue

			transparent = form in self._transport_transparent

			if stype in self._transport_local or transparent:
				pass
			elif stype in self._encoding and not transparent:
				encoder = self._encoding[stype]
				if form == 'value':
					param = encoder(self, param)
				else:
					param = [encoder(self, x) for x in param]
			else:
				# It's not already in representation form nor a transport native value.
				if stype in rio:
					encode = rio[stype][1]
				else:
					encode = str

				if form == 'value':
					form = 'representation'
					param = encode(param)
				elif form == 'v-set':
					form = 'r-set'
					param = list(map(encode, param))
				elif form == 'v-sequence':
					form = 'r-sequence'
					param = list(map(encode, param))

			yield (form, stype, key, param)

	def encode_parameters(self, parameters):
		if isinstance(parameters, dict):
			pi = types.Parameters.from_pairs_v1(parameters.items())
			return isolate(self.encode_parameters_internal(pi))
		elif parameters.empty():
			return None
		else:
			return isolate(self.encode_parameters_internal(parameters.iterspecs()))

	_encoding = {
		'event': encode_event,
		'failure': encode_failure,
		'report': encode_report,
		'message': encode_message,
		'trace': encode_trace,
		'parameters': encode_parameters,
	}

	def decode_event(self, sequence):
		return types.EStruct.from_tuple_v1(sequence)

	def decode_failure(self, sequence):
		event, sparams, strace = sequence

		es = types.EStruct.from_tuple_v1(event)
		params = self.decode_parameters(sparams)
		trace = self.decode_trace(strace)

		return types.Failure((es, params, trace))

	def decode_report(self, sequence):
		event, sparams, strace = sequence

		es = types.EStruct.from_tuple_v1(event)
		params = self.decode_parameters(sparams)
		trace = self.decode_trace(strace)

		return types.Report((es, params, trace))

	def decode_message(self, sequence):
		event, sparams, strace = sequence

		es = types.EStruct.from_tuple_v1(event)
		params = self.decode_parameters(sparams)
		trace = self.decode_trace(strace)

		return types.Message((es, params, trace))

	def decode_trace(self, sequence):
		events = (types.EStruct.from_tuple_v1(x) for x in sequence[0])
		params = (self.decode_parameters(x) for x in sequence[1])

		return types.Trace.from_events_v1(list(zip(events, params)))

	def decode_parameters_internal(self, parameters, rio=core.representation_io):
		for form, stype, key, rvalue in parameters:
			transparent = form in self._transport_transparent

			if stype in self._decoding:
				decoder = self._decoding[stype]

				if form == 'v-set':
					value = set(decoder(self, x) for x in rvalue)
				elif form == 'v-sequence':
					value = [decoder(self, x) for x in rvalue]
				elif form == 'value':
					value = decoder(self, rvalue)
				else:
					# Representation or reference.
					value = rvalue
			elif stype in rio and transparent:
				decoder = rio[stype][0]

				if form == 'r-set':
					value = set(map(decoder, rvalue))
					form = 'v-set'
				elif form == 'r-sequence':
					value = list(map(decoder, rvalue))
					form = 'v-sequence'
				elif form == 'representation':
					value = decoder(rvalue)
					form = 'value'
				else:
					# Reference.
					value = rvalue
			else:
				# Unknown type.
				value = rvalue

			yield form, stype, key, value

	def decode_parameters(self, sequence):
		if sequence is None:
			return types.Parameters({})
		else:
			return types.Parameters.from_specifications_v1(
				self.decode_parameters_internal(integrate(sequence))
			)

	_decoding = {
		'event': decode_event,
		'failure': decode_failure,
		'report': decode_report,
		'message': decode_message,
		'trace': decode_trace,
		'parameters': decode_parameters,
	}

	def prepare(self, sti:typing.Union[types.Roots, types.Trace], version:int=1) -> typing.Tuple[int, str, list]:
		"""
		# Prepare the local status type instance, &sti, for serialization.
		# Returns a tuple consisting of the format version, root status type,
		# and the root status object.

		# Inverse of &interpret.
		"""

		envtype = recursive_types[sti.__class__]
		method = self._encoding[envtype]
		return (version, envtype, method(self, sti))

	def interpret(self, status:typing.Tuple[int, str, list]) -> typing.Union[types.Roots, types.Trace]:
		"""
		# Interpret the previously serialized status objects.
		# Expects &status to a tuple designating the format version, root status type,
		# and the root status object.

		# Inverse of &prepare.
		"""

		version, envtype, root = status
		if version != 1:
			raise ValueError("unsupported format version %d" %(version,))

		return self._decoding[envtype](self, root)

def allocate() -> Transport:
	"""
	# Allocate a &Transport instance using default configuration.
	"""
	return Transport(default_transport_types)
