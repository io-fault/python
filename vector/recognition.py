"""
# System argument vector interpretation methods.

# &legacy is the only implemented method and should cover most use cases.

# [ Events ]
# /`mismatch-unrecognized`/
	# The signalled option did not appear in either index.
# /`mismatch-parameter-restricted`/
	# The long option was given a parameter, but the option takes none.
# /`mismatch-parameter-required`/
	# The option requires a parameter, but no argument was provided.
	# Either due to end of fields or explicit termination.
# /`sequence-append`/
	# Append the option's arguments to the slots.
# /`set-add`/
	# Add the option's argument to the set identified by the slot.
# /`field-replace`/
	# Assign the option's argument to the field identified by the slot.
# /`integer-add`/
	# Add a positive or negative integer to the field identified by the slot.
# /`subdirectory-field-replace`/
	# Using a mapping identified by the slot, assign the key and value extracted
	# from the argument.
"""

class UsageViolation(Exception):
	def __init__(self, mismatch, origin, option, argument=None):
		self.mismatch = mismatch
		self.origin = origin
		self.option = option
		self.argument = argument

	def __str__(self):
		if self.mismatch == 'mismatch-unrecognized':
			msg = f"option {self.option} at index {self.origin} not recognized"
		elif self.mismatch == 'mismatch-parameter-required':
			msg = f"option {self.option} at index {self.origin} requires additional arguments"
		elif self.mismatch == 'mismatch-parameter-restricted':
			msg = f"option {self.option} at index {self.origin} does not take parameters"
		else:
			msg = f"option {self.option} at index {self.origin} caused {self.mismatch!r}"

		return msg

def legacy(restricted, required, options, trap=None, offset=0, signal='-', assignment='='):
	"""
	# Interpret an argument vector, &options, according to the &restricted
	# and &required option indexes. Identified signals are translated into
	# events describing the expected operation, target slot, and value to be
	# processed by a configuration context.

	# The produced events are terminated by a `'remainder'` event containing
	# the excess fields that could not be translated. If all fields were processed
	# as options, the remainder will be an empty list.

	# In the case of an error, the event prior to the remainder will be identified
	# as a mismatch operation with the slot identifying the option that failed
	# to match an index entry.

	# [ Parameters ]
	# /restricted/
		# Mapping designating the options that take no parameters.
	# /required/
		# Mapping designating the options that require one or more parameters.
	# /options/
		# The argument vector to interpret.
	# /trap/
		# Optional slot identifier used when an unrecognized long option
		# is processed. Produces `sequence-append` events.
	# /offset/
		# Defaults to zero; designates the offset to apply to field indexes
		# in order to properly mention a flag or parameter's location.
	# /signal/
		# Defaults to `-`; the character used to identify options in the vector.
	# /assignment/
		# Defaults to `=`; the character used to separate a long option's name
		# from its argument.
	"""
	i = 0
	operator = None
	slot = None
	fields = ()
	ctxopt = None # Primarily for mismatch-parameter-required.

	for i, opt in enumerate(options):
		if fields:
			# Required parameter state.

			yield (operation, fields[0], opt, i+offset)
			del fields[:1]
		elif opt[:1] == signal:
			# Long or Short option.

			if opt[1:2] == signal:
				# Long option.
				pindex = opt.find(assignment)
				if pindex < 0:
					long_arg = None
					long_opt = opt
				else:
					long_arg = opt[pindex+1:]
					long_opt = opt[:pindex]
				ctxopt = long_opt

				if long_opt in required:
					try:
						operation, slot = required[long_opt] #* Long option, single slot.
					except ValueError:
						# This is actually an error with the &required index.
						# Long options are limited to single parameters.
						yield ('mismatch-parameter-required', long_opt, long_arg, i+offset)
						break

					yield (operation, slot, long_arg, i+offset)
				elif long_opt in restricted:
					if long_arg is not None:
						yield ('mismatch-parameter-restricted', long_opt, long_arg, i+offset)
						break

					operation, value, slot = restricted[long_opt]
					yield (operation, slot, value, i+offset)
				elif long_opt == signal:
					# Termination
					if fields:
						# Explicit termination with non-empty &fields.
						assert ctxopt is not None
						yield ('mismatch-parameter-required', ctxopt, fields, i+offset)

					break
				elif trap is not None:
					yield ('sequence-append', trap, (long_opt[2:], long_arg), i+offset)
				else:
					# long_opt was not in any translation index.
					yield ('mismatch-unrecognized', long_opt, long_arg, i+offset)
					break
			elif opt[:2] in required:
				# Short parameterized option.
				operation, *fields = required[opt[:2]]
				ctxopt = opt[:2]

				if len(opt) > 2:
					yield (operation, fields[0], opt[2:], i+offset)
					del fields[:1]
			else:
				# Try short option group.
				ctxopt = opt
				subopts = ((si, signal+x) for si, x in enumerate(opt[1:]))
				for subindex, iopt in subopts:
					if iopt in restricted:
						# Exact selection.
						operation, value, slot = restricted[iopt]
						yield (operation, slot, value, i+offset)
					else:
						# iopt was not in the context index.
						yield ('mismatch-unrecognized', iopt, None, i+offset)
						break
		else:
			# Not a signal; not an option argument.
			if fields:
				# End of arguments with non-empty &fields.
				assert ctxopt is not None
				yield ('mismatch-parameter-required', ctxopt, fields, i+offset)

			break
	else:
		if fields:
			# End of arguments with non-empty &fields.
			assert ctxopt is not None
			yield ('mismatch-parameter-required', ctxopt, fields, i+offset)

		# All arguments were options.
		# Increase index to correctly capture an empty remainder.
		i += 1

	yield ('remainder', None, options[i:], i+offset)

# The default supported operations.
operations = {
	'field-replace': (lambda t, k, v: t.__setitem__(k, v)),
	'sequence-append': (lambda t, k, v: t[k].append(v)),
	'set-add': (lambda t, k, v: t[k].add(v)),
	'subdirectory-field-replace': (lambda t, k, v: t[k].__setitem__(*v.split('='))),
	'integer-add': (lambda t, k, v: t[k].__setitem__(k, t.get(k, 0) + int(v))),
}

def merge(target, events, Operations=operations):
	"""
	# Apply the values provided by &events into &target using
	# the event's operation to select the merge method provided in &Operations.
	"""
	r = None

	for op, slot, value, origin in events:
		if op in Operations:
			Operations[op](target, slot, value)
		elif op == 'remainder':
			r = value
		elif op == 'ignore':
			pass
		else:
			# mismatch case
			raise UsageViolation(op, origin, slot, value)

	return r
