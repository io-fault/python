"""
# Module finder and loader for Factored Projects.
"""
import importlib.machinery

from . import files
from ..project import system as lsf
from ..route.types import Segment

class IntegralFinder(object):
	"""
	# Select an image based on the configured variants querying the connected factor paths.
	"""

	suffixes = ['.py']
	ModuleSpec = importlib.machinery.ModuleSpec
	ExtensionFileLoader = importlib.machinery.ExtensionFileLoader

	class Loader(importlib.machinery.SourceFileLoader):
		"""
		# Loader for compiled Python factors. Compiled modules are not checked
		# against the source unlike Python's builtin loader.
		"""
		_compile = staticmethod(importlib._bootstrap_external._compile_bytecode)

		def __init__(self, bytecode, fullname, path):
			self._bytecode = bytecode
			self._source = path
			super().__init__(fullname, path)

		@classmethod
		def from_nothing(Class, *args):
			"""
			# Create the &Loader instance with &get_code overridden to return
			# a code object created from a `pass` statement.
			"""
			i = Class(*args)
			passed = compile("pass", i._source, "exec")
			i.get_code = (lambda x: passed)
			return i

		def exec_module(self, module):
			module.__file__ = self._source
			module.__cache__ = self._bytecode

			spec = module.__spec__
			if spec.submodule_search_locations:
				module.__path__ = spec.submodule_search_locations

			super().exec_module(module)

		def get_code(self, fullname):
			# Factors being explicitly compiled, code objects
			# are stored directly without pycache headers.
			try:
				with open(self._bytecode, 'rb') as f:
					# It's the build system's job to make sure everything is updated,
					# so don't bother with headers used by Python's builtin caching system.
					bc = f.read()
			except FileNotFoundError:
				return super().get_code(fullname)

			return self._compile(bc, fullname, self._bytecode, source_path=self._source)

		def set_data(self, *args, **kw):
			raise NotImplementedError("factor modules may not be directly updated using the loader")

	def __init__(self,
			python_bytecode_variants,
			extension_variants, *,
			image_suffix='.i',
			image_container_name='.images',
		):
		"""
		# Initialize a finder instance for use with the given variants.
		"""
		self.context = lsf.Context()
		self.index = dict()
		self.image_container_name = image_container_name
		self.image_suffix = image_suffix

		self.python_bytecode_variants = python_bytecode_variants
		self._pbv = Segment.from_sequence([
			image_container_name,
			'-'.join((
				python_bytecode_variants['system'],
				python_bytecode_variants['architecture'],
			))
		])
		self.system_extension_variants = extension_variants
		self._sev = Segment.from_sequence([
			image_container_name,
			'-'.join((
				extension_variants['system'],
				extension_variants['architecture'],
			))
		])

	def connect(self, route:files.Path):
		"""
		# Add the route to finder connecting its subdirectories for import purposes.

		# Similar to adding a filesystem path to Python's &sys.path.
		"""

		pd = self.context.connect(route)
		self.index.update((x, pd) for x in map(str, pd.roots) if x not in self.index)
		return self

	def disconnect(self, route):
		"""
		# Remove a route from the finder's set eliminating any relevant index entries.
		"""

		keys = []
		pds = set()

		for k, v in self.index:
			if v.route == route:
				keys.append(k)
				pds.add(v)

		for k in keys:
			del self.index[k]

		for pd in pds:
			self.context.product_sequence.remove(pd)

		ids = set()
		for key, instance in self.context.instance_cache.items():
			typ, id = key
			if typ == 'project':
				pd = instance.product
			else:
				pd = instance

			if pd in pds:
				ids.add(key)

		for key in ids:
			del self.context.instance_cache[key]

		return self

	@classmethod
	def invalidate_caches(self):
		pass

	def find(self, name):
		"""
		# Retrieve the product with a root that matches the start of the given &name.
		"""
		soa = name.find('.')
		if soa == -1:
			if name not in self.index:
				# Must be root package if there is no leading name.
				return None
			else:
				soa = len(name)

		# Accessible modules are expected to be anchored to the product directory.
		prefix = name[:soa]
		if prefix not in self.index:
			return None

		return self.index[prefix]

	def find_spec(self, name, path, target=None):
		"""
		# Using the &index, check for the presence of &name's initial package.
		# If found, the images contained by the connected directory will be
		# used to load either an extension module or a Python bytecode module.
		"""

		# Project Protocols aren't used as they may require recursive imports.

		pd = self.find(name)
		if pd is None:
			return None

		Loader = self.Loader
		nameparts = name.split('.')
		route = pd.route + nameparts
		ftype = route.fs_type()
		parent = route.container

		pkg = False

		if ftype == 'void':
			# Check for `extensions` factor.

			cur = parent
			while (cur/'extensions').fs_type() == 'void':
				cur = cur.container
				if str(cur) in (str(pd.route), '/'):
					# No extensions.
					break
			else:
				xpath = route.segment(cur)
				exts = cur/'extensions'
				extfactor = exts//xpath

				if extfactor.fs_type() != 'void':
					# .extension entry is present
					ir = (pd.route//self._sev)
					ir //= extfactor.segment(pd.route)
					extpath = str(ir.suffix(self.image_suffix))

					l = self.ExtensionFileLoader(name, extpath)
					spec = self.ModuleSpec(name, l, origin=extpath, is_package=False)
					return spec

		if ftype == 'directory':
			# Not an extension; path is selecting a directory.
			pkg = True
			pysrc = route / '__init__.py'
			module__path__ = str(route)
			nameparts.append('__init__')
			origin = str(pysrc)
			if pysrc.fs_type() == 'void':
				Loader = self.Loader.from_nothing
		else:
			# Regular Python module or nothing.
			for x in self.suffixes:
				pysrc = route.suffix_filename(x)
				if pysrc.fs_type() == 'data':
					break
			else:
				# No recognized sources.
				return None

			module__path__ = str(pysrc.container)
			origin = str(pysrc)

		# Bytecode for {factor}/__init__.py or {factor}.py
		cached = (pd.route//self._pbv)
		cached += nameparts
		cached = cached.suffix(self.image_suffix)

		l = Loader(str(cached), name, str(pysrc))
		spec = self.ModuleSpec(name, l, origin=origin, is_package=pkg)
		spec.cached = str(cached)

		if pkg:
			spec.submodule_search_locations = [module__path__]

		return spec

	@classmethod
	def create(Class, system, python, host, form='executable'):
		"""
		# Construct a standard loader selecting images with the given &form.
		"""

		bc = {
			'system': system,
			'architecture': python,
			'form': form,
		}

		ext = {
			'system': system,
			'architecture': host,
			'form': form
		}

		return Class(bc, ext)

def setup(form='executable', paths=(), platform=None):
	"""
	# Create and install a configured &IntegralFinder.

	# The new finder is assigned to &finder and its &lsf.Context to &context.
	# This is considered process global data and &context the method that should
	# be used to resolve factors that are intended for application support.

	# If called multiple times, a new finder will be created and the assignments
	# will be overwritten. However, the old finder will remain active.
	"""
	global finder, context
	import sys

	if platform is None:
		from . import identity
		system, host = identity.root_execution_context()
		python = identity._python_architecture
	else:
		system, python, host = platform

	finder = IntegralFinder.create(system, python, host, form)
	context = finder.context

	for x in paths:
		if not x:
			# Ignore empty fields.
			continue
		x = files.Path.from_absolute(x)
		finder.connect(x)

	sys.meta_path.insert(0, finder)
	return finder
