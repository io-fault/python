"""
# Weak references tools and subclasses.
"""
import weakref

class Method(weakref.WeakMethod):
	"""
	# &weakref.WeakMethod subclass providing execution methods for the target
	# covering a few signatures.
	"""
	__slots__ = ()

	def _unlinked(self, *args, **kw):
		raise ReferenceError("cannot call method as instance that no longer exists")

	def zero(self):
		"""
		# Execute with no arguments.
		"""
		return (self() or self._unlinked)() # WeakMethod

	def one(self, arg):
		"""
		# Execute with one argument.
		"""
		return (self() or self._unlinked)(arg) # WeakMethod

	def any(self, *args):
		"""
		# Execute with all arguments.
		"""
		return (self() or self._unlinked)(*args) # WeakMethod

	def keywords(self, *args, **kw):
		"""
		# Execute with all arguments and keywords.
		"""
		return (self() or self._unlinked)(*args, **kw) # WeakMethod
