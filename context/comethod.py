from collections.abc import Hashable
from typing import Callable
from types import MethodType

class MethodNotFound(Exception):
	"""
	# Raised by &object.__colookup__ when the given key is not initialized.
	"""

class Type(type):
	__slots__ = ()

	@classmethod
	def __prepare__(Class, name, bases, **kw):
		cm = {}
		for x in bases:
			cm.update(getattr(x, '__comethods__', None) or {})

		def comethodregister(*key):
			def cosetter(func):
				cm[key] = func
				return func
			return cosetter

		return {
			'__comethods__': cm,
			'comethod': comethodregister,
		}

	def __new__(*args, **kw):
		i = type.__new__(*args, **kw)

		# Overwrite comethod and use it for lookup.
		i.comethod = i.__cobind__
		return i

class object(metaclass=Type):
	"""
	# Base class for objects maintaining method aliases.

	# Subclasses of this type will have the `comethod` decorator
	# available in the class body for designating the key that can
	# be used to select the decorated method.

	# After the subclass is created, the metaclass will convert
	# the decorator into the query interface for retrieving methods by
	# their aliases.
	"""

	__slots__ = ()
	__comethods__ = None

	@classmethod
	def __colookup__(Class, *key:Hashable) -> Callable:
		try:
			return Class.__comethods__[key]
		except KeyError:
			pass

		raise MethodNotFound(key)

	def __cobind__(self, *key:Hashable, Method=MethodType) -> MethodType:
		return Method(self.__colookup__(*key), self)

	def comethod(self, *key:Hashable) -> MethodType:
		"""
		# Select the method associated with the given &key.
		"""
		raise RuntimeError("metaclass did not override comethod")
