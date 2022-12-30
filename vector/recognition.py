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
# /`subfield-replace`/
	# Using the mapping identified by the slot, assign the key and value extracted
	# from the argument.
# /`sequence-append-assignment`/
	# Using the sequence identified by the slot, append the tuple representing
	# assignment provided as the argument to the option.
"""

class UsageViolation(Exception):
	"""
	# Exception signalling that options were not properly expressed.

	# [ Properties ]
	# /mismatch/
		# /`'mismatch-unrecognized'`/
			# The option could not be mapped to an action and configuration slot.
		# /`'mismatch-parameter-required'`/
			# The option required a parameter and the argument vector had no more elements.
		# /`'mismatch-parameter-restricted'`/
			# The option was given an argument, but takes zero.
	# /origin/
		# The location of the option as cited by the mismatch event.
	# /option/
		# The identified option being processed.
	# /argument/
		# The option's identified argument if any.
	"""
	def __init__(self, mismatch, origin, option, argument=None):
		self.mismatch = mismatch
		self.origin = origin
		self.option = option
		self.argument = argument

	def __str__(self):
		leading = "option {self.option} at index {self.origin} "
		msg = ({
			'mismatch-unrecognized': "is not a recognized option",
			'mismatch-parameter-required': "requires additional arguments",
			'mismatch-parameter-restricted': "does not take parameters",
		}).get(self.mismatch, "caused {self.mismatch!r}")

		return (leading + msg).format(self=self)

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
						i += 1
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

def _sfr(t, k, i, v):
	subkey, subv = v.split('=', 1)
	t[k][subkey] = i((k, subkey), subv)

def _seq(t, k, i, v):
	subkey, subv = v.split('=', 1)
	t[k].append((subkey, i((k, subkey), subv)))

# The default supported operations.
operations = {
	'field-replace': (lambda t, k, i, v: t.__setitem__(k, i(k, v))),
	'sequence-append': (lambda t, k, i, v: t[k].append(i(k, v))),
	'set-add': (lambda t, k, i, v: t[k].add(i(k, v))),
	'set-discard': (lambda t, k, i, v: t[k].discard(i(k, v))),
	'integer-add': (lambda t, k, i, v: t.__setitem__(k, t.get(k, 0) + int(i(k, v)))),
	'subfield-replace': _sfr,
	'sequence-append-assignment': _seq,
}
del _sfr, _seq

def merge(target, events, Interpreter=(lambda k,s: s), Operations=operations):
	"""
	# Apply the values provided by &events into &target using
	# the event's operation to select the merge method provided in &Operations.

	# [ Parameters ]
	# /target/
		# The object that the interpreted options and arguments are being
		# inserted into. A configuration dictionary.
	# /events/
		# An iterable producing recognized option events.
		# Normally, constructed by &legacy.
	# /Interpreter/
		# A function called with the slot being assigned and value that needs
		# to be interpreted prior to the storage operation.

		# Defaults to a reflection of the given value(no-op).
	# /Operations/
		# A mapping designating how an assignment operation is to be
		# performed against the &target.

		# Defaults to &operations.
	"""
	r = None

	for op, slot, value, origin in events:
		if op in Operations:
			try:
				Operations[op](target, slot, Interpreter, value)
			except Exception as err:
				# &slot is the identified option string for mismatches.
				raise UsageViolation(op, origin, slot, value) from err
		elif op == 'remainder':
			r = value
		elif op == 'ignore':
			pass
		else:
			# mismatch case
			raise UsageViolation(op, origin, slot, value)

	return r
