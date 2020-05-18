"""
# Parse and query locator reference files.
"""

def split(text, _filter=(lambda i: [x for x in i if x and not x[:1] == '#'])):
	header, *body, footer = text.split('\n\t')
	canonical, stem = _filter(header.split('\n'))

	footer = footer.split('\n')
	body.extend(footer[0:1])
	del footer[0:1]
	body = [tuple(x.rsplit(' ', 2)) for x in body if x and not x[:1] == '#']

	return canonical, stem, body, _filter(footer)

def _hash_pair(s):
	index = s.find('#')
	if index == -1:
		return (s, None)
	else:
		return (s[:index], s[index+1:])

def _parse_rtype(fields):
	if len(fields) != 3:
		return (None, None, None), fields
	s = fields[0]

	if s[:1] == '[':
		# Extract resource type.
		typ, suffix = s.split(']', 1) # Type Area not closed.
		typ = typ[1:].strip() # Remove leading '['
	else:
		# No type area.
		suffix = s
		typ = None

	suffix, lpath = _hash_pair(suffix)
	return (typ, suffix, lpath), fields[1:]

def structure(parts):
	canonical, stem, rrecords, footer = parts
	root, hash_method = _hash_pair(canonical[1:])
	rpath, default_apath = _hash_pair(stem)

	mirrors = [x[1:] for x in footer if x[:1] == '=']
	records = [
		(x[0][:2], (x[0][2], x[1][0], x[1][1]))
		for x in [_parse_rtype(y) for y in rrecords]
	]

	# Find integrity specification
	for i, r in zip(range(len(records)), records):
		if r[0][0] is not None and r[0][0][:1] == '#':
			del records[i:i+1]
			hash_method = r[0][0][1:]
			lpath, isize, ihash = r[1]
			break

	return {
		'canonical': root + rpath,
		'root': root,
		'path': rpath,
		'integrity-method': hash_method,
		'referent': (default_apath, int(isize), ihash),
		'representation': records,
		'mirrors': mirrors,
	}

def select(struct:dict, type:str=None, suffix:str=None) -> str:
	"""
	# Select the representation resource to use.
	# If no constraint is supplied, the first representation entry is used.

	# On a match, emits representation metadata followed by the canonical form.
	# If any mirrors are defined, the IRI is constructed against them and emitted
	# in the order that they appeared in the reference file.
	"""

	default_apath = struct['referent'][0]
	xsuffix = ''
	if type is None and suffix is None:
		# Select first if no requirement is supplied.
		(stype, xsuffix), ident = struct['representation'][0]
		iri = struct['path'] + xsuffix
	else:
		for (rtype, rsuffix), ident in struct['representation']:
			rcmp = (rtype if type is None else type, rsuffix if suffix is None else suffix)
			if rcmp == (rtype, rsuffix):
				iri = struct['path'] + rsuffix
				xsuffix = rsuffix
				stype = rtype
				break
		else:
			# No matching entries.
			yield None
			return

	yield (stype, ident[0] or default_apath, ident[1], ident[2])
	yield struct['canonical'] + xsuffix
	for m in struct.get('mirrors', ()):
		yield m + iri

if __name__ == '__main__':
	import sys
	y = (structure(split(sys.stdin.read())))
	meta, ciri, *mirrors = select(y)
	print(ciri)
	if mirrors:
		print("\n".join(mirrors))
