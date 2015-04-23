"""
Mime Type Parser for content types and ranges.

Interfaces here work exclusively with character-strings; wire data must be decoded.
"""
import operator

class Type(tuple):
	"""
	The Content-Type, Subtype, Options triple describing the type of data.

	An IANA Media Type.

	A container interface (``in``) is provided in order to identify if a given
	type is considered to be within another::

	 text/html in */*
	 text/html in text/*
	 text/html;level=1 in text/html
	 text/html not in text/html;level=1
	"""
	__slots__ = ()

	def __str__(self, format = '/'.join):
		if self[2]:
			optstr = ';'
			optstr += ';'.join(
				[
					'='.join((k, v if '"' not in v else '"'+v.replace('"', '\\"')+'"'))
					for k,v in self[2]
				]
			)
		else:
			optstr = ''
		return format(self[:2]) + optstr

	def __bytes__(self):
		return str(self).encode('utf-8')

	@property
	def cotype(self):
		'Content Type: application/, text/, model/, \\*/'
		return self[0]

	@property
	def subtype(self):
		'Subtype: /plain, /xml, /html, /*'
		return self[1]

	@property
	def parameters(self):
		'Parameters such as charset for encoding designation.'
		return self[2]

	@classmethod
	def from_string(typ, string, **parameters):
		"""
		Split on the ';' and '/' separators and build an instance.
		"""
		mtype, *strparams = string.split(';')

		ct, st = map(str.strip, mtype.split('/', 1))

		params = [
			map(str.strip, x.split('=', 1)) for x in strparams
		]
		for i in range(len(params)):
			# handle cases where the parameter had no equal sign with a &None indicator
			p = params[i]
			if len(p) == 1:
				params[i] = (p[0], None)

		# allow for keyword overrides for parameters
		params.extend(parameters.items())

		os = frozenset([tuple(map(str, x)) for x in params])
		return typ((ct,st,os))

	def __contains__(self, mtype):
		if self.cotype in ('*', mtype[0]):
			# content-type match
			if self.subtype in ('*', mtype[1]):
				# sub-type match
				if not self.options or (mtype[2] and mtype[2].issubset(self.options)):
					# options match
					return True
		return False

def parse(header, strip = str.strip,
	typsep = ',', optsep = ';', valsep = '=', quote = '"',
	escape = '\\',
):
	"""
	Generate the media range from the contents of an Accept header.

	Yields:

		[(:py:class:`internet.libmedia.Type`, None or [(k,v),...]),...]

	Where the second item in the yielded tuples is a list of media type options.

	.. note:: This function must be used explicitly by the receiver
				 of the disassembler as parsing this information has costs.
	"""
	# fuck parser generators! we like the pain
	current_type = None
	current_options = []
	current_key = None

	state = typsep
	pos = 0
	end = len(header)

	while pos < end:
		# identify the next option boundary.
		# note: if it's starting at an option value,
		# the next_delimiter may get adjusted
		next_opts = header.find(optsep, pos)
		if next_opts == -1:
			next_opts = end
		next_delimiter = next_opts
		next_type = header.find(typsep, pos, next_delimiter)
		if next_type >= 0:
			next_delimiter = next_type

		if state is None:
			# normally occurs on the edge of a quotation
			state = header[next_delimiter:next_delimiter+1]
			pos = next_delimiter+1
			continue

		if state == typsep:
			if current_type is not None and current_type.strip():
				# starting a new type? yield the previous
				option_dict = dict(current_options)
				quality = option_dict.pop('q', '1.0')
				yield tuple(map(strip, current_type.split('/', 1))), option_dict, quality
				current_options = []
				current_type = None

			current_type = header[pos:next_delimiter]
			pos = next_delimiter + 1
			state = header[next_delimiter:pos]
		else:
			if state == optsep:
				if current_key is not None:
					current_options.append((current_key, None))
				next_value = header.find(valsep, pos, next_delimiter)
				if next_value == -1:
					# no '=' sign..
					current_options.append((header[pos:next_delimiter].strip(), None))
				else:
					next_delimiter = next_value
					# pickup the key
					current_key = header[pos:next_delimiter].strip()

				# next state
				pos = next_delimiter + 1
				state = header[next_delimiter:pos]
			elif state == valsep:
				# handle cases where there's a quoted value
				# must come before the next delimiter.
				next_quote = header.find(quote, pos, next_delimiter)
				if next_quote == -1:
					# not quoted, append
					current_options.append((current_key, header[pos:next_delimiter].strip()))
					pos = next_delimiter + 1
					state = header[next_delimiter:pos]
				else:
					# quoted string
					quotation = ""
					pos = next_quote + 1
					backslash = pos
					while backslash >= 0:
						quotation += header[pos:backslash]
						# ???: \n \r
						if header[backslash:backslash+1] == escape:
							# take the escaped character
							pos = backslash + 2
							quotation += header[backslash+1:pos]
						endquote = header.find(quote, pos)
						# handle escapes
						backslash = header.find(escape, pos, endquote)
					quotation += header[pos:endquote]
					pos = endquote + 1
					current_options.append((current_key, quotation)) # no strip
					state = None
			else:
				raise RuntimeError("impossible state")

	# flush out the remainder
	if current_type is not None:
		option_dict = dict(current_options)
		quality = option_dict.pop('q', '1.0')
		yield tuple(map(strip, current_type.split('/', 1))), option_dict, quality

class Range(tuple):
	"""
	Media Range class for supporting Accept headers.

	Ranges are a mapping of content-types to an ordered sequence of subtype sets.
	The ordering of the subtype sets indicates the relative quality.

	Querying the range for a set of type will return the types with the
	highest precedence for each content type.

	:py:obj:`None` is used to represent '*' types.
	"""
	__slots__ = ()

	@classmethod
	def from_header(typ, header, MediaType = Type):
		l = parse_accept(header)
		return typ()

	@staticmethod
	def parse_options(options, strip = str.strip, tuple = tuple):
		"""
		parse_options(options)

		:param options: Iterator of equality delimited fields.
		:type options: :py:class:`collections.Iterable`

		Parse and strip equality, b'=', delimited key-values.
		"""
		return [tuple(map(strip, f.split('=', 1))) for f in options]

	@classmethod
	def from_bytes(typ, data):
		return typ.from_string(data.decode('utf-8'))

	@classmethod
	def from_string(typ, string,
		skey = operator.itemgetter(0),
	):
		l = []
		for tpair, options, quality in parse(string):
			cotype, subtype = tpair
			percent = int(float(quality) * 100)
			l.append((percent,Type((cotype, subtype, frozenset(options.items())))))
		l.sort(key=skey, reverse=True)
		return typ(l)

	def query(self, *available):
		"""
		Given a sequence of mime types, return the best match
		according to the qualities recorded in the range.
		"""
		current = None
		position = None
		quality = 0
		for x in available:
			# PERF: nested loop sadface O(len(available)*len(self))
			for q, mt in self:
				if x in mt or mt in x:
					if q > quality:
						current = x
						position = mt
						quality = q
					elif q == quality:
						if mt in position:
							# same quality, but has precedence
							current = x
							position = mt
					else:
						if current is not None and q < quality:
							# the range is ordered by quality
							# everything past this point is lower quality
							break
		if current is None:
			return None
		return (current, position, quality)
