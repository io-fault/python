"""
# Parse and query reference composition files.
"""

def form(records):
	rec = []
	for il, r in records:
		if il == 0:
			yield rec
			rec = list(r)
		elif il == 1:
			rec.extend(r)
		elif il > 1:
			rec[-1] = rec[-1] + ' ' + ' '.join(r)
		else:
			# Discard.
			pass

	if rec:
		yield rec

def context(rheader):
	"""
	# Extract the record prefix, qualifiers, and attributes from the header.
	"""
	prefix = rheader[0]
	rattr = []
	rquals = []
	rcurrent = rquals
	for field in rheader[1:]:
		if field[:1] == '[':
			field = field.lstrip('[')
			rcurrent = rattr

		if field[-1:] == ']':
			rcurrent.append(field[:-1])
			rcurrent = rquals
		else:
			rcurrent.append(field)

	return rheader[0], rattr, rquals

def split(text, _filter=(lambda i: [x for x in i if x and not x[:1] == '#'])):
	header, *body, footer = text.split('\n\t')
	canonical, stem = _filter(header.split('\n'))

	footer = footer.split('\n')
	body.extend(footer[0:1])
	body = [(x[:2].count('\t'), x.split()) for x in body]
	del footer[0:1]

	return canonical, stem, body, _filter(footer)

def structure(parts):
	canonical, stem, rrecords, footer = parts

	mirrors = [x[1:] for x in footer if x[:1] == '=']
	rheader = rrecords[0][1] #* No representation header.
	prefix, rattr, rquals = context(rheader)
	annotations, *reprs = form(rrecords[1:])

	return {
		'canonical': canonical[1:],
		'path': stem,
		'prefix': prefix,

		'qualifiers': rquals,
		'annotations': annotations,

		'representation': reprs,
		'resource-attributes': rattr,
		'mirrors': mirrors,
	}

def select(struct:dict, req:dict, *fields:str) -> str:
	"""
	# Select fields from the representation records.
	"""

	keys = {k: i+1 for i, k in enumerate(struct['resource-attributes'])}
	keys['suffix'] = 0
	filters = (lambda x, k: not req[k] == x[keys[k]])

	for record in struct['representation']:
		for k in req:
			if filters(record, k):
				break
		else:
			yield tuple(record[keys[k]] for k in fields)

if __name__ == '__main__':
	import sys
	y = (structure(split(sys.stdin.read())))
	print(y)
	for r in select(y, {'suffix': '.img'}, 'suffix', 'octets'):
		print(r)
