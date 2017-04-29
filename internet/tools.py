"""
# Collection of parsers and formatters that apply to multiple protocols.

# Generally, a supplement for &.libhttp, and a dependency of &.libmedia.
# The tokenization that occurs in &.libhttp is intentionally simple, but
# some of the unparsed fields may need to be structured by the downstream of
# a tokenization instance. Notably, cookie headers make use of parameter
# series that can be processed by &split_parameter_series.

# [ Terminology ]

# The term `rife` is common, but not in this context. Alternative names
# for this module would be `libcommon` or `libshared`. Rife was chosen
# for its distinct qualities.

# [ References ]

# /Cookies
	# &<http://www.ietf.org/rfc/rfc2109.txt>
"""
import itertools

def resolve_backslashes(field:bytes) -> bytes:
	"""
	# Properly resolve backslashes inside `quoted-string` areas.
	"""
	fi = iter(field.split(b'\\'))
	yield next(fi)
	for x in fi:
		if x:
			if x[0] <= 127:
				yield x
			else:
				# Does not match escape pattern in RFC.
				yield b'\\'
				yield x

# Separators + CTL. Presence of these causes quotations.
http_separators = b'()<>@,;:\\\"/[]?={} \t\x7f' + bytes(range(32))
tmap = bytearray(range(256))
for b in http_separators:
	tmap[b] = 0

def _quote(octets,
		tmap=tmap, escaped={b'"', b'\n', b'\r', b'\\', b'\x7f'},
		len=len, bytes=bytes
	):
	# An unfortunate implementation, but the necessary tools
	# for an efficient don't appear to be in the standard library.
	parts = octets.translate(tmap).split(b'\0')
	if len(parts) == 1:
		# No need for quotes.
		yield octets
		return

	ip = parts.__iter__()

	ci = 0
	last = next(ip)
	yield b'"'
	yield last
	ci += len(last)

	for last in ip:
		sep = bytes((octets[ci],))
		if sep in escaped or octets[ci] < 32:
			yield b'\\'
		yield sep
		yield last
		ci += len(last) + 1
	yield b'"'

del tmap, http_separators

def quote(octets):
	"""
	# Discover whether the octets should be quoted and backslash-escape any octets
	# cited as needing escapes. &quote is fairly expensive and should be avoided
	# when possible. Given the case that it is known ahead of time that a quotation
	# is unnecessary, &join_parameter_series.Parameters.quote provided.
	"""
	global _quote
	return b''.join(_quote(octets))

def join_parameter_series(fields, quote=quote):
	"""
	# Given an iterator of key-value pairs, construct a properly escaped
	# parameters series that is commonly used within HTTP headers.

	# The &quote parameter is provided in order to override the escape mechanism
	# given the case that it is known that no escaping need happen.
	"""
	return b';'.join(
		b'='.join(
			(k, quote(v))
		) if v is not None else k
		for k, v in fields
	)

def _normal_parameter_area(more, value_separator=b'=', field_separator=b';'):
	# Used to parse the areas outside of a quoted section.
	return [
		(kv[0].strip(), kv[1].strip() if kv.__len__() > 1 else None)
		for kv in (kv.split(value_separator, 1) for kv in more.split(field_separator) if kv)
	]

def _normal_mediarange_area(more, separator=b',', value_separator=b'=', field_separator=b';'):
	# Identical to parameter_area, but with an extra separator.
	return [
		(kv[0].strip(), kv[1].strip() if kv.__len__() > 1 else None)
		for kv in (
			kv.split(value_separator, 1)
			for kv in (
				itertools.chain.from_iterable(
					p.split(field_separator)
					for p in more.split(separator)
				)
			) if kv
		)
	]

def split_parameter_series(series,
		field_separator=b';',
		value_separator=b'=',
		quotation=b'"',
		escape_character=b'\\',
		empty=b'',
		normal=_normal_parameter_area,
		tuple=tuple, map=map,
	):
	"""
	# Given a series of `;` separated of key-value pairs, return the sequence
	# of key value pairs parsing (rfc:http)`quoted-string` ranges properly.

	# Specification designated invalid character sequences are not checked,
	# and must be handled separately for strict conformance.
	"""
	global resolve_backslashes

	# Normal processing outside quotes.
	fx = normal

	quotes = series.split(quotation)
	if quotes.__len__() == 1:
		# No quotes? This is the fast path.
		yield from fx(quotes[0])
		return

	iq = quotes.__iter__()

	for normal in iq:
		processed = fx(normal) # Unquoted area.
		if not processed:
			continue

		k, v = processed[-1] # v is inside a quoted area.
		del processed[-1]
		yield from processed

		for quoted_area in iq:
			if not quoted_area.endswith(escape_character):
				# End of quote. Go back to normal processing.
				v = empty.join(resolve_backslashes(v+quoted_area))
				break
			else:
				y = quoted_area.rstrip(escape_character)
				c = y.__len__() - quoted_area.__len__()
				if c % 2 == 0:
					# End of quote. Go back to normal processing.
					v = empty.join(resolve_backslashes(v+quoted_area))
					break
				else:
					# quote escape. update entry and
					# continue searching for quotation without an escape.
					v = v + quoted_area + quotation

		# Emit kv-pair that had a quoted value.
		yield (k, v)

def decode_parameters(sequence):
	for k, v in sequence:
		k = k.decode('ascii', 'surrogateescape')
		if v is not None:
			v = v.decode('ascii', 'surrogateescape')
		yield (k, v)

def encode_parameters(sequence):
	for k, v in sequence:
		k = k.encode('ascii', 'surrogateescape')
		if v is not None:
			v = v.encode('ascii', 'surrogateescape')
		yield (k, v)
