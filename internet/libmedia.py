"""
Mime Type Parser for content types and ranges.

Interfaces here work exclusively with character-strings; wire data must be decoded.

[ Data ]

/types
	A mapping of type names and file extensions to MIME type strings.

/filename_extensions
	A mapping of filename extensions to type name.

[ Override ]

/type_from_string

	Construct a &Type instance from a MIME type string.

	Code:
	#!/pl/python
		mt = libmedia.type_from_string("text/xml")

	Equivalent to &Type.from_string, but cached.

/range_from_string

	Construct a &Range instance from a Media Range string like an Accept header.

	Equivalent to &Range.from_string, but cached.
"""
import operator
import functools
import typing

types = {
	'data': 'application/octet-stream', # browsers interpret this as a file download

	'python-pickle': 'application/x-python-object+pickle',
	'python-marshal': 'application/x-python-object+marshal',
	'python-xml': 'application/x-python-object+xml', # fault.xml format
	# 'structures': 'application/x-conceptual+xml',

	'text': 'text/plain',
	'txt': 'text/plain',
	'rtf': 'application/rtf',

	'cache': 'text/cache-manifest',
	'html': 'text/html',
	'htm': 'text/html',
	'css': 'text/css',

	'pdf': 'application/pdf',
	'postscript': 'application/postscript',

	'json': 'application/json',
	'javascript': 'application/javascript',
	'js': 'application/javascript',

	'xml': 'text/xml',
	'sgml': 'text/sgml',

	'rdf': 'application/rdf+xml',
	'rss': 'application/rss+xml',
	'atom': 'application/atom+xml',
	'xslt': 'application/xslt+xml',
	'xsl': 'application/xslt+xml',

	'zip': 'application/zip',
	'gzip': 'application/gzip',
	'gz': 'application/gzip',
	'bzip2': 'application/x-bzip2',
	'tar': 'application/x-tar',
	'xz': 'application/x-xz',
	'rar': 'application/x-rar-compressed',
	'sit': 'application/x-stuffit',
	'z': 'application/x-compress',

	'tgz': 'application/x-tar+gzip',
	'txz': 'application/x-tar+x-xz',
	'torrent': 'application/x-bittorrent',

	# images
	'svg': 'image/svg+xml',
	'png': 'image/png',
	'gif': 'image/gif',
	'tiff': 'image/tiff',
	'tif': 'image/tiff',
	'jpeg': 'image/jpeg',
	'jpg': 'image/jpeg',

	# video
	'mpg': 'video/mpeg',
	'mpeg': 'video/mpeg',
	'mp2': 'video/mpeg',
	'mov': 'video/quicktime',
	'mp4': 'video/mp4',
	'webm': 'video/webm',
	'ogv': 'video/ogg',
	'avi': 'video/avi',

	# audio
	'aif': 'audio/x-aiff',
	'aiff': 'audio/x-aiff',
	'mp3': 'audio/mpeg',
	'wav': 'audio/x-wav',
	'mid': 'audio/midi',

	'ogg': 'audio/ogg',
	'opus': 'audio/ogg',
	'oga': 'audio/ogg',
	'ogx': 'application/ogg',
	'spx': 'audio/ogg',

	# microsoft
	'xls': 'application/vnd.ms-excel',
	'doc': 'application/msword',
	'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
	'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
	'ppsx': 'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
	'potx': 'application/vnd.openxmlformats-officedocument.presentationml.template',
}

@functools.lru_cache(32)
def file_type(filename):
	"""
	Identify the MIME type from a filename using common file extensions.

	Unidentified extensions will likely return application/octets-stream.
	"""
	global types

	parts = filename.rsplit('.', 1)

	if parts[1] not in types:
		return Type.from_string(types['data'])

	return Type.from_string(types[parts[1]])

class Type(tuple):
	"""
	The Content-Type, Subtype, Options triple describing the type of data.

	An IANA Media Type.

	A container interface (`in`) is provided in order to identify if a given
	type is considered to be within another:

		- text/html in */*
		- text/html in text/*
		- text/html;level=1 in text/html
		- text/html not in text/html;level=1
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

	def push(self, subtype):
		"Return a new &Type with the given &subtype appended to the instance's &.subtype"

		cotype, ssubtype, *remainder = self

		return self.__class__((cotype, '+'.join(ssubtype, subtype))+remainder)

	def pop(self):
		"Return a new &Type with the last '+'-delimited subtype removed. (inverse of push)"

		cotype, ssubtype, *remainder = self
		index = ssubtype.rfind('+')

		if index == -1:
			# nothing to pop
			return self

		return self.__class__((cotype, ssubtype[:index]) + remainder)

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
				if not self.parameters or (mtype[2] and mtype[2].issubset(self.parameters)):
					# options match
					return True
		return False

def parse(header,
		typsep = ',', optsep = ';', valsep = '=', quote = '"',
		escape = '\\',
		strip=str.strip, map=map, len=len, tuple=tuple,
	):
	"""
	Generate the media range from the contents of an Accept header.

	Yields: `[(internet.libmedia.Type, None or [(k,v),...]),...]`

	Where the second item in the yielded tuples is a list of media type options.

	! NOTE:
		This function must be used explicitly by the receiver
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

	&None is used to represent '*' types.
	"""
	__slots__ = ()

	@staticmethod
	def parse_options(options:typing.Iterable, strip = str.strip, tuple = tuple):
		"""
		Parse and strip equality, b'=', delimited key-values.

		[ Parameters ]

		/options
			Iterator of equality delimited fields.
		"""

		return [tuple(map(strip, f.split('=', 1))) for f in options]

	@classmethod
	def from_bytes(typ, data, encoding='utf-8'):
		"""
		Instantiate the Range from a bytes object; decoded and passed to &from_string.
		"""

		return typ.from_string(data.decode(encoding))

	@classmethod
	def from_string(typ, string,
			skey = operator.itemgetter(0),
		):
		"""
		Instantiate the Range from a Python string.
		"""

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

any_type = Type(('*', '*', frozenset()))
any_range = Range([(100, any_type)])

# Cached constructors.
type_from_string = functools.lru_cache(32)(Type.from_string)
range_from_string = functools.lru_cache(32)(Range.from_string)
