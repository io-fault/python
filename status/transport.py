"""
# Transport protocol implementation for identified data sets.
"""

def prepare(value, separator='\n', Type=str, Convert=str):
	"""
	# Convert a value into a form suitable for sequencing.
	"""

	if isinstance(value, (int, float)):
		return Convert(value).split(separator)
	elif isinstance(value, Type):
		return value.split(separator)
	else:
		return value

def isolate(lines:str, separator='\n\t'):
	"""
	# Separate &lines into parts that can be processed by &identify.
	"""
	seq = []

	# Split on the escapes used to continue the slot content portion first.
	for l in lines.split(separator):
		# Process normal lines slot-content.
		*subs, final = l.split('\n')
		if subs:
			if seq:
				seq.extend(subs[:1])
				yield seq
				seq = []
				del subs[:1]

			for s in subs:
				if s:
					yield [s]
			# retain final in case of escapes
			seq = [final]
		else:
			if final:
				seq.append(final)

	if seq and seq[0]:
		yield seq

def identify(iseq, separator=': '):
	"""
	# Identify the slots and content of a transmission processed by &isolate.
	"""

	for s in iseq:
		if not s:
			continue

		try:
			field, initial = s[0].split(separator, 1)
			s[0] = initial
		except ValueError:
			# No space, no initial content.
			field, initial = s[0].split(separator[:1], 1)
			assert initial == ""
			del s[:1]

		yield (field, s)

def structure(lines:str, separator='\n\t'):
	return identify(isolate(lines, separator))

def sequence(pairs, empty=''):
	buf = empty
	for k, v in pairs:
		l = len(v)
		if l == 0:
			continue

		if l == 1:
			v = v[0]
		else:
			v = '\n\t'.join(v)

		buf += k + ': ' + v + '\n'
	return buf
