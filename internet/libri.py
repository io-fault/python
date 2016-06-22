"""
Parse and Serialize Structured Resource Indicators

As with many implementations in `internet`, libri is not strict with regards
to a particular specification. Rather, it seeks to handle all cases with relative
sanity such that any error checking may be performed by the user.
"""

import re
import collections

pct_encode = '%%%0.2X'.__mod__
unescaped = '%' + ''.join([chr(x) for x in range(0, 33)])

percent_escapes_re = re.compile('(%[0-9a-fA-F]{2,2})+')

escape_re = re.compile('[%s]' %(re.escape(unescaped),))
escape_user_re = re.compile('[%s]' %(re.escape(unescaped + ':@/?#'),))
escape_password_re = re.compile('[%s]' %(re.escape(unescaped + '@/?#'),))

escape_host_re = escape_port_re = escape_path_re = \
	re.compile('[%s]' %(re.escape(unescaped + '/?#'),))
escape_query_key_re = re.compile('[%s]' %(re.escape(unescaped + '&=#'),))
escape_query_value_re = re.compile('[%s]' %(re.escape(unescaped + '&#'),))

percent_escapes = {}
for x in range(256):
	k = '%0.2X'.__mod__(x)
	percent_escapes[k] = x
	percent_escapes[k.lower()] = x
	percent_escapes[k[0].lower() + k[1]] = x
	percent_escapes[k[0] + k[1].lower()] = x

scheme_chars = '-.+0123456789'
del x

def unescape(x, mkval=chr, len=len, isinstance=isinstance):
	"""
	Substitute percent escapes with literal characters.
	"""

	nstr = type(x)('')
	if isinstance(x, str):
		mkval = chr

	pos = 0
	end = len(x)
	while pos != end:
		newpos = x.find('%', pos)
		if newpos == -1:
			nstr += x[pos:]
			break
		else:
			nstr += x[pos:newpos]

		val = percent_escapes.get(x[newpos+1:newpos+3])
		if val is not None:
			nstr += mkval(val)
			pos = newpos + 3
		else:
			nstr += '%'
			pos = newpos + 1
	return nstr

def re_pct_encode(m):
	return pct_encode(ord(m.group(0)))

Parts = collections.namedtuple("Parts",
	('type', 'scheme', 'netloc', 'path', 'query', 'fragment')
)

def split(iri):
	"""
	Split an IRI into its base components based on the markers:

		(: | ://), /, ?, #

	Returns the top-level parts of the IRI as a namedtuple.

	[ Parameters ]
	/iri
		A complete IRI or URI.
	"""
	type = None
	scheme = None
	netloc = None
	path = None
	query = None
	fragment = None

	s = iri.lstrip()
	pos = 0
	end = len(s)

	# absolute IRIs
	if s.startswith("//"):
		pos = 2
		type = "relative" # scheme is defined by context.
	else:
		scheme_pos = s.find(':')
		if scheme_pos == -1:
			# No ':' at all. No scheme spec whatsoever.
			type = "none"
		else:
			# Look for following slashes
			if s.startswith('://', scheme_pos):
				type = "authority"
				pos = scheme_pos + 3
			else:
				# just a ':'
				type = "absolute"
				pos = scheme_pos + 1
			scheme = s[:scheme_pos]

			# validate the scheme.
			for x in scheme:
				if not (x in scheme_chars) and \
				not ('A' <= x <= 'Z') and not ('a' <= x <= 'z'):
					# it's not a valid scheme
					pos = 0
					scheme = None
					type = "amorphous"
					break

	end_of_netloc = end

	path_pos = s.find('/', pos)
	if path_pos == -1:
		path_pos = None
	else:
		end_of_netloc = path_pos

	query_pos = s.find('?', pos)
	if query_pos == -1:
		query_pos = None
	elif path_pos is None or query_pos < path_pos:
		path_pos = None
		end_of_netloc = query_pos

	fragment_pos = s.find('#', pos)
	if fragment_pos == -1:
		fragment_pos = None
	else:
		if query_pos is not None and fragment_pos < query_pos:
			query_pos = None
		if path_pos is not None and fragment_pos < path_pos:
			path_pos = None
			end_of_netloc = fragment_pos
		if query_pos is None and path_pos is None:
			end_of_netloc = fragment_pos

	if end_of_netloc != pos:
		netloc = s[pos:end_of_netloc]
		# just digits? assume amorphous: host:port
		if type == 'absolute' and netloc.isdigit():
			netloc = scheme + ':' + netloc
			scheme = None
			type = 'amorphous'

	if path_pos is not None:
		path = s[path_pos+1:query_pos or fragment_pos or end]

	if query_pos is not None:
		query = s[query_pos+1:fragment_pos or end]

	if fragment_pos is not None:
		fragment = s[fragment_pos+1:end]

	return Parts(type, scheme, netloc, path, query, fragment)

def join_path(p, _re = escape_path_re, _re_pct_encode = re_pct_encode):
	"""
	Join a list of paths(strings) on "/" *after* escaping them.
	"""

	if not p:
		return None
	return '/'.join([_re.sub(re_pct_encode, x) for x in p])

unsplit_path = join_path

def split_path(p, fieldproc = unescape):
	"""
	Return a list of unescaped strings split on "/".

	Set `fieldproc` to `str` if the components' percent escapes should not be
	decoded.
	"""

	if p is None:
		return []
	return [fieldproc(x) for x in p.split('/')]

def join(t):
	"""
	Make an RI from a split RI(5-tuple)
	"""

	s = ''
	if t[0] == 'authority':
		s += t[1] or ''
		s += '://'
	elif t[0] == 'absolute':
		s += t[1] or ''
		s += ':'
	elif t[0] == 'relative':
		s += '//'

	if t[2] is not None:
		s += t[2]
	if t[3] is not None:
		s += '/'
		s += t[3]
	if t[4] is not None:
		s += '?'
		s += t[4]
	if t[5] is not None:
		s += '#'
		s += t[5]
	return s

unsplit = join

def split_netloc(netloc, fieldproc = unescape):
	"""
	Split a net location into a 4-tuple, (user, password, host, port).

	Set `fieldproc` to `str` if the components' percent escapes should not be
	decoded.
	"""

	pos = netloc.find('@')
	if pos == -1:
		# No user information
		pos = 0
		user = None
		password = None
	else:
		s = netloc[:pos]
		userpw = s.split(':', 1)
		if len(userpw) == 2:
			user, password = userpw
			user = fieldproc(user)
			password = fieldproc(password)
		else:
			user = fieldproc(userpw[0])
			password = None
		pos += 1

	if pos >= len(netloc):
		return (user, password, None, None)

	pos_chr = netloc[pos]
	if pos_chr == '[':
		# IPvN addr
		next_pos = netloc.find(']', pos)
		if next_pos == -1:
			# unterminated IPvN block
			next_pos = len(netloc) - 1
		addr = netloc[pos:next_pos+1]
		pos = next_pos + 1
		next_pos = netloc.find(':', pos)
		if next_pos == -1:
			port = None
		else:
			port = fieldproc(netloc[next_pos+1:])
	else:
		next_pos = netloc.find(':', pos)
		if next_pos == -1:
			addr = fieldproc(netloc[pos:])
			port = None
		else:
			addr = fieldproc(netloc[pos:next_pos])
			port = fieldproc(netloc[next_pos+1:])

	return (user, password, addr, port)

def join_netloc(t):
	"""
	Create a netloc fragment from the given tuple(user,password,host,port).
	"""

	if t[0] is None and t[2] is None:
		return None
	s = ''
	if t[0] is not None:
		s += escape_user_re.sub(re_pct_encode, t[0])
		if t[1] is not None:
			s += ':'
			s += escape_password_re.sub(re_pct_encode, t[1])
		s += '@'

	if t[2] is not None:
		s += escape_host_re.sub(re_pct_encode, t[2])
		if t[3] is not None:
			s += ':'
			s += escape_port_re.sub(re_pct_encode, t[3])

	return s

unsplit_netloc = join_netloc

def parse_query(query, fieldproc=unescape):
	return [
		tuple((list(map(fieldproc, x.split('=', 1))) + [None])[:2])
		for x in query.split('&')
	]

def structure(t, fieldproc=unescape, tuple=tuple, list=list, map=map):
	"""
	Create a dictionary from a split RI(5-tuple).

	Set `fieldproc` to `str` if the components' percent escapes should not be
	decoded.
	"""
	global parse_query
	global split_netloc

	d = {}

	# type determines inclusion of scheme, so absence no
	# longer indicates anything
	d['type'] = t[0]
	d['scheme'] = t[1]

	if t[2] is not None:
		uphp = split_netloc(t[2], fieldproc = fieldproc)
		if uphp[0] is not None:
			d['user'] = uphp[0]
		if uphp[1] is not None:
			d['password'] = uphp[1]
		if uphp[2] is not None:
			d['host'] = uphp[2]
		if uphp[3] is not None:
			d['port'] = uphp[3]

	if t[3] is not None:
		if t[3]:
			d['path'] = list(map(fieldproc, t[3].split('/')))
		else:
			d['path'] = []

	if t[4] is not None:
		if t[4]:
			d['query'] = parse_query(t[4], fieldproc=fieldproc)
		else:
			# no characters followed the '?'
			d['query'] = []

	if t[5] is not None:
		d['fragment'] = fieldproc(t[5])
	return d

def construct_query(x,
		key_re = escape_query_key_re,
		value_re = escape_query_value_re,
	):
	"""
	Given a sequence of (key, value) pairs, construct.
	"""

	return '&'.join([
		v is not None and \
		'='.join((
			key_re.sub(re_pct_encode, k),
			value_re.sub(re_pct_encode, v),
		)) or \
		key_re.sub(re_pct_encode, k)
		for k, v in x
	])

def construct(x):
	"""
	Construct a RI tuple(5-tuple) from a dictionary object.
	"""

	p = x.get('path')
	if p is not None:
		p = '/'.join([escape_path_re.sub(re_pct_encode, y) for y in p])
	q = x.get('query')
	if q is not None:
		q = construct_query(q)
	f = x.get('fragment')
	if f is not None:
		f = escape_re.sub(re_pct_encode, f)

	u = x.get('user')
	pw = x.get('password')
	h = x.get('host')
	port = x.get('port')

	return (
		x.get('type'),
		x.get('scheme'),

		# netloc: [user[:pass]@]host[:port]
		join_netloc((
			x.get('user'),
			x.get('password'),
			x.get('host'),
			x.get('port'),
		)),
		p, q, f
	)

def parse(iri, structure = structure, split = split, fieldproc = unescape):
	"""
	Parse an RI into a dictionary object. Synonym for `structure(split(x))`.

	Set &fieldproc to &str if the components' percent escapes should not be
	decoded.
	"""

	return structure(split(iri), fieldproc = fieldproc)

def serialize(x, join = join, construct = construct):
	"""
	Return an RI from a dictionary object. Synonym for `join(construct(x))`.
	"""

	return join(construct(x))

def http(struct):
	"""
	Return the HTTP Request-URI suitable for submission with an HTTP request.
	"""

	if "path" in struct:
		p = join_path(struct["path"]) or "/"
	else:
		p = "/"

	if "query" in struct:
		q = construct_query(struct["query"])
		return "?".join((p, q))

	return p
