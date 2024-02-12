"""
# Data structures for holding failure, notification, and trace information.

# [ Constructor Versioning ]

# The class methods of the types here are given version numbers. New versions of methods
# can be introduced at any time without the immediate or eventual depcrecation of older versions.
# Generally, they should be usable into perpetuity aside from some unforeseen exception and in
# such a case, deprecation warnings will be used prior to their removal.
"""
import typing
from collections.abc import Mapping

class EStruct(tuple):
	"""
	# Structure holding a snapshot of core information regarding an event that is likely to be
	# displayed to a user or emitted to a log. While this has been generalized to identify events,
	# it's name was chosen to lend to its suitability for errors.

	# Fields can be omitted, but instances should contain as much information as possible.
	# &EStruct instances are snapshots that may be serialized prior to formatting, so
	# instances should be made with the consideration that the final endpoint may not
	# have access to more advanced formatting routines.
	"""
	__slots__ = ()

	def __repr__(self) -> str:
		return ("<[%s#%s] %s: %r>" % (self[0], self[3], self[1], self[4]))

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
	def from_string_v1(Class, erstring, protocol='http://if.fault.io/status/unspecified'):
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

class Frame(tuple):
	"""
	# A status frame designating a serializable event and associated context.
	"""
	__slots__ = ()

	@property
	def f_protocol(self) -> str:
		"""
		# The event's protocol.
		"""
		return self.f_event.protocol

	@property
	def f_channel(self) -> str:
		"""
		# The channel designated by the frame.
		"""
		return self[0]

	@property
	def f_event(self) -> EStruct:
		"""
		# The qualified identification of the frame event.
		"""
		return self[1]

	@property
	def f_extension(self) -> Mapping[str, str]:
		"""
		# The data extension associated with the frame.
		"""
		return self[2]

	@property
	def f_image(self) -> str:
		"""
		# The visible message of the status frame.
		"""
		return self.f_event.abstract

	@classmethod
	def from_string_v1(Class, espec:str, channel=None, extension=None, /,
			protocol='http://if.fault.io/status/frames',
			_EStruct=EStruct.from_string_v1,
		):
		"""
		# Create using an &EStruct string and optional context.
		"""
		return Class((channel, _EStruct(espec, protocol=protocol), extension))

	@classmethod
	def from_event_v1(Class, event:EStruct, channel=None, extension=None):
		"""
		# Create using an &EStruct instance and optional context.
		"""
		return Class((channel, event, extension))
