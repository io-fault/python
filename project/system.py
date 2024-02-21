"""
# Product and Project directory protocol support.

# Provides three classes of interest: &Project, &Product, and &Context.
# Context manages a project set formed from a sequence of Products that make up a factor search path;
# Projects are cached on Context instances and Products primarily provide access and updates to a
# product directory's index, the (filename)`.product` directory.

# Even in the case of single product directories, a Context should be used to access the projects.
# The primary function of a &Product instance is to merely provide access to the data stored in the index,
# not as a general purpose abstraction for interacting with the product directory as that function usually
# involves multiple directories, an abstraction provided by &Context.
"""
import typing
import collections
import operator
import itertools

from ..context import tools
from ..route.types import Selector, Segment
from . import types

def parse_project_index(lines:typing.Iterable[str]):
	"""
	# Generate tuples from the given space separated fields, &lines.
	# Intended to be interpreted as a dictionary, the items' initial element should
	# be the project's (universal) identifier. The second element is a tuple of the
	# local name and project protocol identifier.
	"""
	for l in lines:
		l = l.strip().split()
		yield (l[0], (types.factor@l[1],) + tuple(l[2:]))

def parse_protocol_declaration(text:str):
	"""
	# Split the text and return the fields as a tuple.
	"""
	return tuple(text.split())

def structure_project_declaration(text:str, nl="\n"):
	"""
	# Parse the contents of a `.project` file.

	# [ Returns ]
	# A pair, the project protocol and a &types.Information instance.
	"""
	fields = text.split(nl, maxsplit=2)

	identity = fields[0] #* No project identity line.
	name, iid, protocol = identity.split()

	try:
		entity = fields[1].strip() #* No contact entity.
	except (IndexError, KeyError):
		auth = contact = None
	else:
		# Similar to formal e-mail addresses, but limited
		# to an entity name and contact IRI or mail address.
		if entity[-1] != '>':
			auth = entity.strip()
			contact = None
		else:
			auth, contact = entity.rsplit('<', 1)
			auth = auth.strip()
			contact = contact.strip('<>').strip()
			if contact == '-':
				contact = None

		if auth in {'-', '- -'}:
			auth = None

	return protocol, types.Information(
		iid, name, auth, contact,
	)

def sequence_project_declaration(protocol, project, /, nl="\n", fs=" "):
	"""
	# Format the contents of a `.project` file from the given protocol and
	# &types.Information structure.
	"""
	heading = [
		fs.join([project.name, project.identifier, protocol]),
		fs.join([(project.authority or '-'), '<' + (project.contact or '-') + '>'])
	]

	return nl.join(heading) + nl

def scan_product_directory(read_protocol, route:Selector, limit=1024*4):
	"""
	# Identify the projects within the given route.
	# Usually only used through &Product.update.
	"""
	i = 0
	stack = collections.deque([route])

	while stack:
		current = stack.popleft()

		for d in current.fs_iterfiles('directory'):
			i += 1
			if i > limit:
				raise RuntimeError("filesystem scan limit exceeded")

			if '.' in d.identifier:
				continue

			p = read_protocol(d)
			if p is not None:
				fp = types.FactorPath.from_sequence(d.segment(route))
				yield (p[0], (fp,) + p[1:])
			else:
				stack.append(d)

# Project (factor interpretation) Protocol implementations.
protocols = {
	'factors/polynomial-1': (__package__ + '.polynomial', 'V1'),
}

class Product(object):
	"""
	# Project set root providing access to contexts and projects.

	# While often annotated as &Selector, usually filesystem operation must be
	# supported by the selector.
	"""

	project_identity_segment = Segment.from_sequence(['.project', 'f-identity'])
	default_meta_directory = Segment.from_sequence(['.product'])
	default_images_directory = Segment.from_sequence(['.images'])

	@classmethod
	def import_protocol(Class, identifier:str) -> types.FactorIsolationProtocol:
		"""
		# Retrieve the protocol class using the &identifier.
		"""
		module_name, classname = protocols[identifier]
		import importlib
		module = importlib.import_module(module_name)
		return getattr(module, classname)

	@property
	def project_index_route(self, filename='PROJECTS') -> Selector:
		"""
		# Materialized project index file path.
		"""
		return self.cache/filename

	@property
	def connections_index_route(self, filename='CONNECTIONS') -> Selector:
		"""
		# Connection list fulfilling requirements.
		"""
		return self.cache/filename

	@property
	def connections(self):
		"""
		# The requirements of the product as a sequence of product directory routes.

		# This sequence is not cached and constructed at access time by opening the
		# file &connections_index_route.
		"""
		rpath = self.route.container
		try:
			paths = self.connections_index_route.get_text_content()
		except FileNotFoundError:
			return []
		else:
			return list(rpath@x for x in paths.split('\n') if x)

	def clear(self):
		"""
		# Remove the instance local cache.
		"""
		self.local = {}
		self.projects = {}
		self.roots = set()

	def __init__(self, route:Selector, limit:int=1024*4, cache:Selector=None):
		"""
		# Initialize a &Product using &route with an empty local instance cache.

		# &cache parameter is available as an override for the (filename)`.product`
		# directory location, but should normally not be used.
		"""
		self.clear()
		self.route = route.delimit()
		self.limit = limit

		if cache is None:
			self.cache = self.route // self.default_meta_directory

	def __hash__(self):
		return hash(self.route)

	def __eq__(self, operand):
		return self.route == operand.route

	def image(self, variants:types.Variants, project:types.FactorPath, factor:types.FactorPath, suffix='.i'):
		"""
		# Identify the location of the factor's image for the given &variants.
		"""

		if variants.form != 'executable':
			path = self.route / ('.' + variants.form)
		else:
			path = self.route // self.default_images_directory
		path /= (variants.system + '-' + variants.architecture)

		path //= project
		path = path.delimit()
		path //= factor

		return path.suffix(suffix)

	def identifier_by_factor(self, factor:types.FactorPath) -> typing.Tuple[str, types.FactorIsolationProtocol]:
		"""
		# Select the project identifier and protocol using a factor path (to the project).
		# Uses the instance local cache populated by &load or &update.
		"""
		ids, proto = self.local[factor]
		return ids, self.import_protocol(proto)

	def factor_by_identifier(self, identifier:str) -> typing.Tuple[types.FactorPath, types.FactorIsolationProtocol]:
		"""
		# Select the factor path (to the project) and protocol using the project identifier.
		# Uses the instance local cache populated by &load or &update.
		"""
		ids, proto = self.projects[identifier]
		return ids, self.import_protocol(proto)

	def select(self, constraint:types.FactorPath) -> typing.Iterable[types.FactorPath]:
		"""
		# Retrieve project (path) entries that have the given prefix, &constraint.

		# If the argument identifies a context, generate the projects contained therein.
		# If the argument is a nil &types.FactorPath, generate all project paths.
		"""

		if constraint in self.local:
			yield constraint
		elif len(constraint) == 0:
			yield from self.local
		else:
			l = len(constraint)
			cl = list(constraint)
			for k, v in self.local.items():
				if list(k)[:l] == l:
					yield k

	def read_protocol(self, route:Selector):
		"""
		# Retrieve the protocol data from the configured &project_declaration_filesnames.
		"""
		src = route // self.project_identity_segment
		# Discard Information instance as callers only need (id, proto).
		try:
			protocol, pi = structure_project_declaration(src.get_text_content())
		except (FileNotFoundError, NotADirectoryError):
			return None

		return (pi.identifier, protocol)

	@property
	def _spec(self):
		return (self.read_protocol, self.route)

	def load(self):
		"""
		# Load the snapshot of the projects from the product's route.
		"""

		with self.project_index_route.fs_open('tr') as f:
			prj = dict(parse_project_index(f.readlines()))

		local = {v[0]: (k,) + v[1:] for k, v in prj.items()}

		self.projects = prj
		self.local = local
		self.roots = set(list(k)[0] for k in local)

		return self

	def store(self, SortKey=operator.itemgetter(0), Chain=itertools.chain.from_iterable):
		"""
		# Store the snapshot of the projects to the product's route.
		"""

		if self.cache.fs_type() != 'directory':
			self.cache.fs_mkdir()

		prjseq = [(k,) + v for k, v in self.projects.items()]
		prjseq.sort(key=SortKey)
		with self.project_index_route.fs_open('tw') as f:
			f.writelines(Chain(' '.join(map(str, x))+'\n' for x in prjseq))

		return self

	def update(self):
		"""
		# Update the snapshot of the projects by querying the filesystem.
		# The effects of this should be recorded with a subsequent call to &store.
		"""
		projects = {
			fp: pj
			for fp, pj in scan_product_directory(*self._spec, limit=self.limit)
		}

		local = {v[0]: (k,) + v[1:] for k, v in projects.items()}

		self.projects = projects
		self.local = local
		self.roots = set(list(x)[0] for x in local)

		return self

	def iterprojects(self, limit=2048, prefix=types.factor):
		"""
		# Query the route and retrieve all projects within the product.

		# Results may be inconsistent with the instance cache.
		"""
		i = 0
		start = self.route//prefix
		stack = collections.deque()

		p = self.read_protocol(start)
		if p is not None:
			return p + (start,)

		stack.append(start)

		while stack:
			current = stack.popleft()
			for d in current.fs_iterfiles('directory'):
				i += 1
				if i > limit:
					raise RuntimeError("filesystem scan limit exceeded")

				p = self.read_protocol(d)
				if p is None:
					stack.append(d)
				else:
					yield p + (d,)

	def split(self, fpath:types.FactorPath):
		"""
		# Separate the project portion from &fpath.
		# Returns a pair of &types.FactorPath; the project and the factor.
		"""
		if fpath in self.local:
			return (fpath, types.factor)

		suffix = str(fpath)
		for x in self.local:
			xstr = str(x)
			if suffix.startswith(xstr + '.'):
				return (x, types.factor@suffix[len(xstr)+1:])

class Project(object):
	"""
	# Project Interface joining relavant routes and protocol instances.
	"""
	meta_directory_path = Segment.from_sequence(['.project'])

	@tools.cachedproperty
	def meta(self):
		"""
		# The directory containing project metadata.
		"""
		return self.route // self.meta_directory_path

	def __init__(self, pd:Product, pi:str, pf:types.FactorPath, proto:types.FactorIsolationProtocol):
		self.product = pd
		self.protocol = proto

		self.identifier = pi
		self.factor = pf

		# This is unconditional. &Product only organizes Projects relative to
		# its directory. Filesystem symbolic links must be used to control redirects.
		self.route = (self.product.route // pf)

	@tools.cachedproperty
	def _iid_corpus_name_pair(self):
		p = self.identifier.rstrip('/').rsplit('/', 1)
		if len(p) < 2:
			# If there is no '/', presume it's just a name.
			p.insert(0, '')
		return tuple(p)

	@property
	def corpus(self) -> str:
		"""
		# The leading portion of the independent identifier.
		"""
		return self._iid_corpus_name_pair[0]

	@property
	def name(self) -> str:
		"""
		# The name of the project as defined by the independent identifier.
		"""
		return self._iid_corpus_name_pair[1]

	def requirements(self, context):
		"""
		# Identify the unique set of projects required by this project.
		"""
		u = set()
		refs = {}

		for (fp, ft), (fr, fs) in self.select(types.factor):
			if str(ft) == 'http://if.fault.io/factors/meta.references':
				refkey = types.Reference(self.identifier, fp)
				for fmt, refset in fs:
					refs[refkey] = list(map(
						(lambda x: types.Reference.from_ri(None, x)),
						filter(bool, refset.get_text_content().split('\n'))
					))

			for r in fr:
				if r in u:
					continue
				else:
					u.add(r)

		# Identify project set.
		p = set()
		for r in u:
			if r in refs:
				# Expand local references.
				for xr in refs[r]:
					if xr not in u:
						p.add(xr)
			elif r.project != self.identifier:
				p.add(r)
		return p

	@tools.cachedproperty
	def information(self) -> types.Information:
		"""
		# The identifying information of the project.
		"""
		return self.protocol.information(self.route)

	@tools.cachedproperty
	def extensions(self) -> types.Extensions:
		"""
		# Additional identifying information of the project.
		"""
		return types.Extensions(
			self.icon().decode('utf-8') or None,
			self.synopsis().decode('utf-8') or None,
		)

	def icon(self) -> bytes:
		"""
		# Read the icon reference contained in (system/file)`.project/icon`.

		# [ Returns ]
		# /(syntax/python)`b''`/
			# When the filesystem resource could not be loaded or when
			# only whitespace is present.

			# Exceptions are suppressed.
		# /&bytes/
			# The data content of the `self.meta / 'icon'` filesystem resource
			# as read by &files.Path.fs_load.
		"""
		try:
			return (self.meta / 'icon').fs_load().strip()
		except Exception:
			return b''

	def synopsis(self) -> bytes:
		"""
		# Read the synopsis data contained in (system/file)`.project/synopsis`.

		# [ Returns ]
		# /(syntax/python)`b''`/
			# When the filesystem resource could not be loaded or when
			# only whitespace is present.

			# Exceptions are suppressed.
		# /&bytes/
			# The data content of the `self.meta / 'synopsis'` filesystem resource
			# as read by &files.Path.fs_load.
		"""
		try:
			return (self.meta / 'synopsis').fs_load().strip()
		except Exception:
			return b''

	def image(self, variants, fp:types.FactorPath, suffix='.i'):
		return self.product.image(variants, self.factor, fp, suffix=suffix)

	def select(self, factor:types.FactorPath):
		"""
		# Retrieve factors within the given path.
		"""
		for (fp, ft), fd in self.protocol.iterfactors(self.refer, self.route, factor):
			yield ((factor//fp, ft), fd)

	def split(self, fp:types.FactorPath, chain=itertools.chain):
		"""
		# Separate the factor path from the element path.
		# Returns a pair, &types.FactorPath and a &str; the project and the factor.
		"""

		xstr = str(fp)
		last = fp
		for p in chain(~fp.container, (types.factor,)):
			for ((f, t), srcdata) in self.select(p):
				if f == last:
					return (f, xstr[len(str(f)) + 1:])

			last = p

		return None

	def fullsplit(self, qpath:types.FactorPath):
		"""
		# Separate the project path, factor path, and fragment path
		# from the given fully qualified factor path.
		"""
		pj, fp = self.product.split(qpath)
		fp, fm = self.split(fp)
		return (pj, fp, fm)

	def refer(self, factorpath:str, *, context:types.FactorPath=None) -> types.Reference:
		"""
		# Construct a &types.Reference instance using the given &factorpath.
		"""

		if context is not None:
			context = self.factor // context
		else:
			context = self.factor / 'project'

		fp = types.fpc(context, factorpath, root=self.factor)

		pjfp, fp = self.product.split(fp)
		return types.Reference(self.product.local[pjfp][0], fp)

class Context(object):
	"""
	# &Product and &Project instance cache and search path.
	"""

	@classmethod
	def import_protocol(Class, identifier:str) -> typing.Type[types.FactorIsolationProtocol]:
		"""
		# Retrieve the protocol class using the &identifier.
		"""
		module_name, classname = protocols[identifier]
		import importlib
		module = importlib.import_module(module_name)
		return getattr(module, classname)

	@classmethod
	def from_product_connections(Class, pd:Product):
		"""
		# Create a &Context initializing it with the immediate connections identified by &pd.
		"""
		i = Class()
		for pdr in pd.connections:
			i.connect(pdr)
		return i

	def __init__(self):
		self.product_sequence = []
		self.instance_cache = {}

	def connect(self, route:Selector) -> Product:
		"""
		# Add a new Product instance to the context.

		# Returns an existing &Product instance if the route was in the cache, otherwise
		# creates a new instance and places it in the cache.
		"""
		key = ('product', route)
		if key in self.instance_cache:
			return self.instance_cache[key]

		pd = Product(route)
		pd.load()

		self.product_sequence.append(pd)
		self.instance_cache[key] = pd
		return pd

	def project(self, id:str) -> Project:
		"""
		# Retrieve a &Project instance from the context's instance cache.

		# [ Exceptions ]
		# /&LookupError/
			# No project with the given identifier has been loadded in the context.
		"""
		return self.instance_cache[('project', id)]

	def iterprojects(self) -> typing.Iterable[Project]:
		"""
		# Generate &Project instances cached from a prior &load call.

		# This includes any Context Projects.
		"""
		for key, pj in self.instance_cache.items():
			if key[0] == 'project':
				yield pj

	def load(self):
		"""
		# Fully populate the instance cache with all of the projects from
		# all of the connected products.
		"""
		for pd in reversed(self.product_sequence):
			for id, (fp, proto_id) in pd.projects.items():
				key = ('project', id)
				proto = self.import_protocol(proto_id)
				self.instance_cache[key] = Project(pd, id, fp, proto({}))

	def configure(self):
		"""
		# Traverse the cached projects and apply protocol inheritance.
		"""

		# Configure protocol data.
		for pj in (v for k, v in self.instance_cache.items() if k[0] == 'project'):
			pj.protocol.configure(pj.route)

	def index(self, product:Selector):
		"""
		# Find the index of the &Product whose route is equal to &product.
		"""
		for i, x in enumerate(self.product_sequence):
			if x.route == product:
				return i

	def split(self, qpath:types.FactorPath):
		"""
		# Identify the product, project, and factor path of the given &qpath.
		# Returns a triple identifying the &Product, &Project, and remaining &types.FactorPath.

		# [ Parameters ]
		# /qpath/
			# The qualified factor path identifying an element, factor, or project.
		"""
		pd = None
		for pd in self.product_sequence:
			parts = pd.split(qpath)
			if parts is not None:
				break
		else:
			raise LookupError("no such project in context")

		pj, fp = parts
		iid = pd.identifier_by_factor(pj)
		pj = self.project(iid[0])

		return (pd, pj, fp)

	def image(self, variants, fp, suffix='.i'):
		pd, pj, lfp = self.split(fp)
		return pd.image(variants, pj.factor, lfp, suffix=suffix)

	def refer(self, factorpath:str, *, context:types.FactorPath=types.factor):
		"""
		# Construct a &types.Reference from the given &factorpath string.

		# &factorpath is first processed with &types.fpc before being
		# analyzed by &split.
		"""
		pd, pj, factor = self.split(types.fpc(context, factorpath))
		return types.Reference(pj.identifier, factor)

if __name__ == '__main__':
	import sys
	from ..system import files
	from .polynomial import V1
	poly = V1({})
	print(sys.argv)
	for x in map(files.Path.from_absolute, sys.argv[1:]):
		info = poly.information(x)
		info.contact = info.contact.strip('<>')
		dotproject = sequence_project_declaration('factors/polynomial-1', info)
		with (x/'.project').fs_open('w') as f:
			f.write(dotproject)
