"""
# Data structures for holding failure, notification, and trace information.

# [ Constructor Versioning ]

# The class methods of the types here are given version numbers. New versions of methods
# can be introduced at any time without the immediate or eventual depcrecation of older versions.
# Generally, they should be usable into perpetuity aside from some unforeseen exception and in
# such a case, deprecation warnings will be used prior to their removal.
"""
import typing

# &.core and other local modules are not imported here in order to keep overhead low.
# It is desireable to be able to use these in annotations without importing I/O dependencies.

class EStruct(tuple):
	"""
	# Structure holding a snapshot of core information regarding an event that is likely to be
	# displayed to a user or emitted to a log. While this has been generalized to identify events,
	# it's name was chosen to lend to its suitability for errors.

	# While fields can be omitted, instances should contain as much information as possible.
	# &EStruct instances are snapshots that may be serialized prior to formatting, so
	# instances should be made with the consideration that the final endpoint may not
	# have access to more advanced formatting routines.
	"""
	__slots__ = ()

	def __repr__(self) -> str:
		if str(self.code) != self.identifier:
			return ("<[%s#%s:%d] %s: %r>" % self)
		else:
			return ("<[%s#%s] %s: %r>" % (self[0], self[1], self[3], self[4]))

	@property
	def protocol(self) -> str:
		"""
		# The IRI or symbol identifying the set of events that this instance belongs to.
		# The authority specifying the semantics and metadata of the event.

		# If the IRI is real, it should contain routing information that will
		# provide aid in properly formatting the event information. If the IRI is not real,
		# the application processing the event should have formatting rules available.

		# Symbolic identifiers can be used, but should normally map to a IRI
		# prior to serialization.

		# This field *must not* be localized.
		"""
		return self[0]

	@property
	def identifier(self) -> str:
		"""
		# A string unambiguously identifying the event.
		# Also recognized as the preferred string representation of &code that can identify the event.
		# Formally referred to as "String Identifier".

		# This must *not* be the symbolic name assigned to the &code.
		# For instance, the POSIX errno define (id)`EINTR` should be considered a &symbol,
		# not an &identifier.

		# For events with integer identifiers, this is normally the decimal representation string.
		# If the &protocol commonly refers to a different representation for the &code,
		# then that string representation should used instead of the decimal string.

		# This field *must not* be localized.
		"""
		return self[1]

	@property
	def code(self) -> int:
		"""
		# The integer form of the &identifier or zero if none exists.
		# Formally referred to as "Integer Code".

		# Often, this is redundant with the &identifier field aside from the data type.

		# However, when the event's integer code is not normally presented or referenced to in
		# decimal form, the redundancy allows the use of the proper form without having
		# knowledge of the routine used to translate between the integer code and the usual
		# string representation. SQL state codes being a notable example where having
		# both forms might have some benefit during reporting.

		# A value of zero *should* indicate that there is no integer form;
		# normally, using the &identifier is the preferred key when
		# resolving additional metadata regarding the event.
		"""
		return self[2]

	@property
	def symbol(self) -> str:
		"""
		# The symbolic name, label, or title used to identify the event.

		# Often, a class name. This is distinct from &identifer and &code in that
		# it is usually how the &identifier was originally selected. For instance,
		# for a POSIX system error, errno, this might be (id)`EAGAIN` or (id)`EINTR`.

		# In cases where an error is being represented that has a formless &protocol,
		# the symbol may be the only field that can be used to identify the event.

		# This field *must not* be localized.
		"""
		return self[3]

	@property
	def abstract(self) -> str:
		"""
		# Single sentence message describing the event.
		# Often a constant string defined by the &protocol, but potentially
		# overridden by the application.

		# This field may be localized, but it is preferrable to use a consistent
		# language that is common to the majority of the application's users.

		# There is the potential that the &protocol can be used to resolve
		# a formatting routine for the display such that this message will not be shown.

		# This field should *not* contain formatting codes.
		# For high-level descriptions, the adapters implemented by a Reporting Pipeline
		# should be used to create friendlier, human-readable abstracts.
		"""
		return self[-1]

	@classmethod
	def from_fields_v1(Class,
			protocol:str,
			symbol:str='Unspecified',
			abstract:str="event snapshot created without abstract",
			identifier:str='',
			code:int=0,
		):
			return Class((protocol, identifier, code, symbol, abstract))

	@classmethod
	def from_tuple_v1(Class, fields):
		"""
		# Create an instance using &fields; expects five objects in this order:

		# # Protocol as a string.
		# # String Identifier of Event.
		# # Integer Code of Event.
		# # Symbol String.
		# # Abstract Paragraph.
		"""
		return Class(fields[:5])

	@classmethod
	def from_arguments_v1(Class, protocol:str, identifier:str, code:int, symbol:str, abstract:str):
		"""
		# Create an instance using the given arguments whose positioning is consistent
		# with where the fields are stored in the tuple.
		"""
		return Class((protocol, identifier, code, symbol, abstract))

	@classmethod
	def from_string_v1(Class, erstring, protocol="http://if.fault.io/status/unspecified"):
		"""
		# Create an EStruct using a string following the format:
		# (illustration)`SYMBOL[str-id int-code]: Abstract`.

		# The protocol keyword can be used to designate the &protocol field.
		"""
		l, f = erstring.split(':', 1)
		sym, ids = l.split('[', 1) # Requires brackets: ERRSYM[]: ...
		idparts = ids.split(' ', 1)

		if len(idparts) > 1:
			idstr, idint = idparts
			idint = int(idint.strip(']'))
		else:
			idstr, = idparts
			idstr = idstr.strip(']')

			try:
				idint = int(idstr)
			except:
				idint = -1

		return Class((protocol, idstr, idint, sym, f.strip()))

class Parameters(object):
	"""
	# A mutable finite-map whose values are associated with the typeform used by transports.

	# [ Properties ]
	# /Specification/
		# Class-level annotation signature for a fully-qualified parameter.
		# A tuple consisting of the necessary information for defining a parameter.

		# # Form, &.core.forms.
		# # Type, &.core.types.
		# # Key, &str identifier used for addressing the parameter.
		# # Value or Representation, &object.
	"""
	__slots__ = ('_storage',)

	# Form, Type, Key, Value
	Specification = typing.Tuple[str, str, str, object]

	_status_type_identifier = 'parameters'
	# Mapping for set_parameters and others that detect the Parameter typeform.
	_python_builtins = {
		bool: 'boolean',
		int: 'integer',
		float: 'rational',
		str: 'string',
		bytes: 'octets',
		type(None): 'void',
		dict: 'parameters',
	}

	@classmethod
	def identify_object_typeform(Class, obj:object, type=type) -> str:
		"""
		# Select a form and type for the given object.
		"""

		# Fast Path
		if type(obj) in Class._python_builtins:
			return ('value', Class._python_builtins[type(obj)])
		elif hasattr(obj, '_status_type_identifier'):
			return ('value', obj._status_type_identifier)

		first = None
		try:
			i = iter(obj)
			first = next(i)
		except StopIteration:
			raise ValueError("empty iterator cannot be used to identify parameter type")
		except Exception:
			# Probably not a collection.
			pass
		else:
			tf = Class.identify_object_typeform(first)
			assert tf[0] in ('value', 'representation',)

			# XXX: Ideally, use an ABC so registrations could be used.
			if isinstance(obj, set):
				return ('v-set', tf[1])
			else:
				return ('v-sequence', tf[1])

		# Cover subclass cases.
		for Type, stype in Class._python_builtins.items():
			if isinstance(obj, Type):
				return ('value', stype)

	def __init__(self, storage):
		self._storage = storage

	def __contains__(self, ob:str):
		return ob in self._storage

	def iterspecs(self) -> typing.Iterable[Specification]:
		"""
		# Emit &Specification items for all the contained parameters.
		"""
		for k, (t, v) in self._storage.items():
			yield t[0], t[1], k, v

	def __eq__(self, operand):
		return operand._storage == self._storage

	# Mapping Interfaces
	def __setitem__(self, key, value):
		self.set_parameter(key, value)

	def __getitem__(self, key):
		return self.get_parameter(key)

	def get(self, key, fallback=None):
		if key in self._storage:
			return self._storage[key][-1]
		return fallback

	def update(self, pairiter):
		idtf = self.identify_object_typeform

		for k, v in pairiter:
			tf = idtf(v)
			self._storage[k] = (tf, v)

	def specify(self, iterspec:typing.Iterable[Specification]):
		"""
		# Update the parameters using an iterator of Specifications.
		"""
		s = self._storage
		s.update({k:((form,typ),v) for form,typ,k,v in iterspec})

	def empty(self) -> bool:
		"""
		# Whether the instance has any parameters.
		"""
		return (not bool(self._storage))

	def list_parameters(self) -> typing.Iterable[str]:
		"""
		# The iterator of parameter names stored within the instance.
		"""
		return self._storage.keys()

	def get_parameter(self, key:str) -> object:
		"""
		# Get the parameter identified by &key.

		# Represented values are *not* interpreted and only the subject is returned.
		"""
		return self._storage[key][-1]

	def set_parameter(self, key:str, value:object):
		"""
		# Set the parameter identified by &key to &value.
		# If the parameter already exists, it will be overwritten and its
		# typeform-value pair returned.

		# The given &value is checked by &identify_object_typeform in order
		# to select a suitable typeform for the parameter.
		"""
		tf = self.identify_object_typeform(value)

		last = self._storage.pop(key, None)
		self._storage[key] = (tf, value)

		return last

	def set_excluded(self, key:str, value:object):
		"""
		# Store an object in the parameter set that will *not* be included
		# in any transmission of the parameters.

		# [ Engineering ]
		# ! TENTATIVE: subject may be removed.
		"""
		self._storage[key] = (('value', 'excluded'), value)

	def set_reference(self, key:str, target:str) -> str:
		"""
		# Configure the parameter identified with &key to refer to the parameter
		# identified with &target.

		# Returns the resolved target's type.
		"""

		t = self._storage[target][0][1]
		self._storage[key] = (('reference', t), target)
		return t

	def set_identifier(self, key:str, value:str):
		"""
		# Set the parameter as an identifier.
		"""
		self._storage[key] = (('value', 'identifier'), value)

	def set_system_file(self, key:str, value:object):
		"""
		# Set parameter as a system file.
		"""
		self._storage[key] = (('value', 'system-file-path'), value)

	def set_rvalue(self, type:str, key:str, value:str):
		"""
		# Set the parameter &key to &value identified as a
		# represented &type. Retrieving this parameter will always
		# give the represented form, but transports will likely
		# convert it to a value upon reception given that it is a
		# recognized type.

		# Primarily used to circumvent any conversion performed by
		# the serialization side of a transport.
		"""
		last = self._storage.pop(key, None)
		self._storage[key] = (('representation', type), str(value))

		return last

	def set_rset(self, type:str, key:str, strings:typing.Iterable[str], Collection=set):
		"""
		# Set the parameter identified by &key to a new &list
		# constructed from the &strings iteratable.

		# The parameter's type is set from &type and its form
		# constantly `'r-set'` identifying it as a set of
		# representation strings.
		"""
		self._storage[key] = (('r-set', type), Collection(strings))

	def set_rsequence(self, type:str, key:str, strings:typing.Iterable[str], Collection=list):
		"""
		# Set the parameter identified by &key to a new &list
		# constructed from the &strings iteratable.

		# The parameter's type is set from &type and its form
		# constantly `'r-sequence'` identifying it as a set of
		# representation strings.
		"""
		self._storage[key] = (('r-sequence', type), Collection(strings))

	@classmethod
	def from_nothing_v1(Class, Storage=dict):
		"""
		# Create an empty set of Parameters.
		"""
		return Class(Storage())

	@classmethod
	def from_pairs_v1(Class, iterpairs:typing.Iterable[typing.Tuple[str, object]]):
		"""
		# Create from a regular Python objects whose values imply the snapshot type.
		"""

		tf = Class.identify_object_typeform
		return Class({k:(tf(v),v) for k,v in iterpairs})

	@classmethod
	def from_specifications_v1(Class, iterspec:Specification):
		"""
		# Create from an iterable producing the exact storage specifications.
		# Likely used in cases where the present fields are constantly defined.
		"""

		return Class({k:((form,typ),v) for form,typ,k,v in iterspec})

	@classmethod
	def from_relation_v1(Class, attributes, types, tuples, titles=None):
		"""
		# Create an instance encoding a single relation.

		# Primarily intended for use with &Report instances.
		"""

		src = {
			'Type': (('value', 'string'), 'relation'),
			'Attributes': (('v-sequence', 'identifier'), attributes),
			'Titles': (('v-sequence', 'string'), titles),
		}

		vectors = []
		add = vectors.append
		for attname, atttype in zip(attributes, types):
			v = list()
			add(v.append)
			src[attname] = (('v-sequence', atttype), v)

		for t in tuples:
			for ainsert, v in zip(vectors, t):
				ainsert(v)

		return Class(src)

	def select(self, attconstraints:typing.Iterable[str]) -> typing.Iterable[typing.Tuple]:
		"""
		# Select the tuples from the encoded relation restricting the produced
		# tuples to the attributes listed in &attconstraints.

		# If &attcontraints is &None, all attributes will be selected.

		# The attributes of the tuples produced will be in the order that they appear
		# in &attconstraints. An attribute may be selected multiple times.

		# ! RELATION: &from_relation_v1
		"""
		s = self._storage
		keys = (attconstraints if attconstraints is not None else s['Attributes'][-1])

		return zip(*[s[x][-1] for x in keys])

	def insert(self, tuples:typing.Iterable[typing.Tuple]):
		"""
		# Insert a set of tuples into the encoded relation.

		# ! RELATION: &from_relation_v1
		"""
		s = self._storage
		appends = [s[x][-1].append for x in s['Attributes'][-1]]

		for t in tuples:
			for ainsert, v in zip(appends, t):
				ainsert(v)

class Trace(tuple):
	"""
	# A sequence of events identifying a location.
	# Primarily used for storing stack traces, but paths of any sort can be identified.

	# [ Engineering ]
	# Currently, this only contains the route stack and is essentially an envelope.
	# Future changes may add data fields, but it is unlikely and this will primarily
	# exist for interface purposes.
	"""
	__slots__ = ()
	_status_type_identifier = 'trace'

	@property
	def t_route(self) -> [(EStruct, Parameters)]:
		"""
		# The serializeable identification of the error's context.
		# A sequence of &EStruct instances associated with a snapshot of
		# relavent metadata.
		"""
		return self[0]

	@classmethod
	def from_events_v1(Class, events:[(EStruct, Parameters)]):
		"""
		# Typed constructor populating the primary field.
		"""
		return Class((events,))

	@classmethod
	def from_nothing_v1(Class):
		"""
		# Create Trace with no route points.
		"""
		return Class(([],))

def _from_string_constructor(Class, erstring:str,
		context:typing.Optional[Trace]=None,
		parameters=None,
		protocol="http://if.fault.io/status/unspecified"
	):

	if context is None:
		context = Trace.from_nothing_v1()
	if parameters is None:
		parameters = Parameters.from_nothing_v1()
	es = EStruct.from_string_v1(erstring, protocol=protocol)

	return Class((es, parameters, context))

class EType(tuple):
	"""
	# Base class for &EStruct based structures.

	# Provides a single generic attribute for accessing the &EStruct.
	"""
	__slots__ = ()

	@property
	def event(self) -> EStruct:
		return self[0]

	@property
	def _status_type_corefields(self) -> tuple:
		return self

class Failure(EType):
	"""
	# Data structure referencing the &EStruct detailing the error that occurred causing
	# an Identified Operation to fail. The &f_parameters contains additional information
	# regarding the &f_error that occurred.
	"""
	__slots__ = ()
	_status_type_identifier = 'failure'

	@property
	def f_context(self) -> Trace:
		"""
		# The serializeable identification of the error's context.
		# A sequence of &EStruct instances associated with a snapshot of
		# relavent metadata.
		"""
		return self[-1]

	@property
	def f_error(self) -> EStruct:
		"""
		# The serializeable identification and information of the cause of the failure.
		"""
		return self[0]

	@property
	def f_parameters(self) -> Parameters:
		"""
		# The relevant parameters involved in the execution of the transaction.
		# Usually, these parameters should be restricted to those that help
		# illuminate the production of the &f_error.
		"""
		return self[1]

	from_string_v1 = classmethod(_from_string_constructor)

	@classmethod
	def from_arguments_v1(Class, errcontext:typing.Optional[Trace], error:EStruct, **parameters):
		"""
		# Create using context and error positional parameters, and
		# error parameters from the given keywords.

		# Signature is identical to &Failure.from_arguments_v1 and &Message.from_arguments_v1.
		"""
		if errcontext is None:
			errcontext = Trace.from_nothing_v1()
		return Class((error, Parameters.from_pairs_v1(parameters.items()), errcontext))

class Message(EType):
	"""
	# Message event associated with an origin context and additional parameters.
	"""
	__slots__ = ()
	_status_type_identifier = 'message'

	@property
	def msg_context(self) -> Trace:
		"""
		# The context of the origin of the message.
		"""
		return self[-1]

	@property
	def msg_event(self) -> EStruct:
		"""
		# The event identifying the message.
		"""
		return self[0]

	@property
	def msg_parameters(self) -> Parameters:
		"""
		# Relevant message parameters.
		"""
		return self[1]

	from_string_v1 = classmethod(_from_string_constructor)

	@classmethod
	def from_arguments_v1(Class, msgctx:typing.Optional[Trace], msgid:EStruct, **parameters):
		"""
		# Create message instance using positional arguments and parameters from keywords.

		# Signature is identical to &Failure.from_arguments_v1 and &Report.from_arguments_v1.
		"""
		if msgctx is None:
			msgctx = Trace.from_nothing_v1()
		return Class((msgid, Parameters.from_pairs_v1(parameters.items()), msgctx))

class Report(EType):
	"""
	# Data structure referencing the &EStruct detailing the report that has been generated.
	# The report's contents resides within the &r_parameters.
	"""
	__slots__ = ()
	_status_type_identifier = 'report'

	@property
	def r_context(self) -> Trace:
		"""
		# The context of the origin of the message.
		"""
		return self[-1]

	@property
	def r_event(self) -> EStruct:
		"""
		# The event identifying the message.
		"""
		return self[0]

	@property
	def r_parameters(self) -> Parameters:
		"""
		# Relevant message parameters.
		"""
		return self[1]

	from_string_v1 = classmethod(_from_string_constructor)

	@classmethod
	def from_arguments_v1(Class, re_ctx:typing.Optional[Trace], report_id:EStruct, **parameters):
		"""
		# Create report instance from arguments.
		# Signature is identical to &Failure.from_arguments_v1 and &Message.from_arguments_v1.
		"""
		if re_ctx is None:
			re_ctx = Trace.from_nothing_v1()
		return Class((report_id, Parameters.from_pairs_v1(parameters.items()), re_ctx))

Roots = typing.Union[
	Message,
	Failure,
	Report,
]

def corefields(st:Roots) -> typing.Tuple[EStruct, Parameters, Trace]:
	"""
	# Retrieve the event structure, parameter set, and context trace
	# from the root type &st.

	# Currently, this returns &st directly as &Message, &Failure, and &Report
	# share the same tuple structure which is consistent with &corefields
	# signature.
	"""
	return st._status_type_corefields
