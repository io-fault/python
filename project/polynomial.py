"""
# Extensible project protocol for filesystem directories.
"""
import typing
import collections
import itertools
import functools

from ..context.types import Cell
from ..route.types import Segment, Selector
from ..system import files

from . import types

# Directory Structure of Integrals
default_image_segment = [['system', 'architecture'], []]
unknown_factor_type = types.Reference(
	'http://if.fault.io/factors', types.factor@'meta.unknown',
	'type', None
)
image_factor_type = types.Reference(
	'http://if.fault.io/factors', types.factor@'meta.image',
	'type', None
)
references_factor_type = types.Reference(
	'http://if.fault.io/factors', types.factor@'meta.references',
	'type', None
)
system_factor_type = types.Reference(
	'http://if.fault.io/factors', types.factor@'system.references',
	'type', None
)

def load_formats(file, *, continued='\t', separator='\n', Ref=types.Reference.from_ri):
	if file.fs_type() == 'void':
		return

	i = iter(file.get_text_content().split(separator))
	typctx = next(i)
	for l in i:
		if not l or l.strip()[:1] == '#':
			# Comments and empty lines.
			continue

		if l[:1] != continued:
			typctx = l
			continue
		else:
			fields = l.split(' ')
			ityp, ext = fields[0].split('.', 1)
			if len(fields) == 2:
				# Implied language class.
				fmtc = typctx.rsplit('/', 1)[1]
				fmts = fields[-1]
			else:
				fmtc = fields[-1]
				fmts = fields[-2]

		ft = Ref('type', typctx + '.' + ityp.strip()).isolate(fmtc + '.' + fmts)
		yield ext.strip('.'), ft

def factor_images(project:Selector, factor:Segment, directory='__f-int__'):
	"""
	# Retrieve the set of images produced by the &factor contained by &project.
	# A segment path is used to identify the factor in order to emphasize that
	# a direct file path should not be used.
	"""
	path = project // factor
	return (path * directory).delimit()

def compose_image_path(groups, default, variants, name, suffix):
	"""
	# Create a variant path (list of strings) according to the given &groups and &variants.
	"""
	segments = []

	for g in groups[:-1]:
		fields = ([(variants.get(x) or default) for x in g])
		segment = '-'.join(fields)
		segments.append(segment)

	if variants.get('form'):
		segments.append(variants.get('form'))

	# Final identifier.
	fields = [name]
	fields.extend((variants.get(x) or default) for x in groups[-1])
	if suffix:
		fields.append(suffix)
	segments.append('.'.join(fields))

	return segments

def structure_factor_declaration(text, nl="\n"):
	"""
	# Split a `.factor` file into a type and symbol set pair.
	"""
	fields = iter(text.strip().split(nl))
	typ = next(fields) #* Empty .factor file?
	return typ, set(filter(bool, (x.strip() for x in fields)))

def parse_image_descriptor_1(string:str) -> typing.Iterator[typing.Sequence[str]]:
	"""
	# Given the data from a (system/filename)`fields.txt` file located inside
	# a factor image set directory, return an iterator producing sequences that
	# detail the groupings used to designate the location of a variant.

	# Normally unused as the default groupings are encouraged.

	# [ Parameters ]
	# /string/
		# The text format is newline separated records consisting of whitespace separated fields.
		# Each line containing fields designates a directory level that will contain
		# the variants expressed on subsequent lines. The final record designating the
		# variants used to specify the image file, often this should be "name".

		# No escaping mechanism is provided as the fields are required to be identifiers.
	"""

	for line in map(str.strip, string.split('\n')):
		if line[:1] in ('#', ''):
			# Ignore comments and empty lines.
			continue

		# Strip the fields in each group ignoring empty fields.
		yield [x for x in map(str.strip, line.split()) if x]

class V1(types.FactorIsolationProtocol):
	"""
	# polynomial-1 protocol implementation.
	"""

	identifier = 'polynomial-1'
	# Segments noting the position of significant files in a polynomial directory.
	FactorDeclarationSignal = Segment.from_sequence(['.factor'])
	FormatsProjectPath = Segment.from_sequence(['.project', 'polynomial-1'])

	def configure(self, route):
		"""
		# Inherit information and configuration from a context project.
		"""

		if 'source-extension-map' not in self.parameters:
			self.parameters['source-extension-map'] = dict()

		if 'type-requirements' not in self.parameters:
			self.parameters['type-requirements'] = dict()

		extmap = []
		typreq = []

		for ext, ft in load_formats(route // self.FormatsProjectPath):
			if ext:
				extmap.append((ext, ft))

		try:
			extmap.extend(context.parameters['source-extension-map'].items())
		except Exception:
			# Ignore most errors here.
			# Resetting extmap for safety may be appropriate, but it is not clear.
			pass

		extmap.extend(self.parameters['source-extension-map'].items())
		self.parameters['source-extension-map'] = dict(extmap)

	def image(self, route:types.Path, variants, fp:types.FactorPath, *,
			default='void',
			groups=default_image_segment,
			suffix='i'
		) -> Selector:
		"""
		# Retrieve the location of the factor's image for the given variants.
		"""
		idir = factor_images(route, fp)
		seg = compose_image_path(groups, default, variants, fp.identifier, suffix)
		return (idir + seg)

	def isource(self, route:files.Path):
		"""
		# Determine if the route is a possible source file for a factor.
		"""
		has_delimiter = ('.' in route.identifier)

		if has_delimiter:
			if route.identifier.startswith('.'):
				# File with leading `.`
				return False
		else:
			# file has no extension to identify its project local type.
			if route.fs_type() == 'data':
				return False

		return True

	def source_format_resolution(self):
		"""
		# Construct a resolution (type) cache for the source extension map.
		"""

		try:
			mapping = self.parameters['source-extension-map']
		except KeyError:
			# No map available.
			return (lambda x: unknown_factor_type)
		else:
			return functools.lru_cache(16)(lambda x: mapping.get(x, unknown_factor_type))

	def type_requirement_resolution(self, /, empty=set()):
		"""
		# Construct a resolution (type requirement) cache for the type requirements.
		"""

		try:
			mapping = self.parameters['type-requirements']
		except KeyError:
			# No map available.
			return (lambda x: empty)
		else:
			return functools.lru_cache(16)(lambda x: mapping.get(x, empty))

	def indirect_factor_records(self, typcache, paths:typing.Iterable[files.Path],
			*, _nomap={}, _default=(unknown_factor_type, set()),
		):
		"""
		# Given an iterable of paths identifying Indirectly Typed Factors, resolve their
		# type reference, factor type, and symbols using the given &typcache.
		"""

		for p in paths:
			# Normalize path; the delimited partition may be used by callers.
			src = p.container.delimit() / p.identifier

			name, suffix = src.identifier.split('.')
			typref = typcache(suffix)
			yield (name, typref.isolate(None)), (set(), Cell((typref, src)))

	def collect_explicit_sources(self, typcache, route:files.Path):
		"""
		# Collect source files paired with their type reference for an
		# Explicitly Typed Factor record.
		"""

		# Excluding dot-directories.
		files = (
			x[1] for x in route.fs_index('data')
			if not x[0].identifier.startswith('.')
		)

		# Excluding dot-files.
		for y in itertools.chain.from_iterable(files):
			if not y.identifier.startswith('.'):
				yield (typcache(y.extension), y)

	def iterfactors(self, refer, route:files.Path, rpath:types.FactorPath,
			*, ignore=types.ignored,
		) -> typing.Iterable[types.FactorType]:
		"""
		# Query the project &route for factor specifications contained within &rpath.
		"""

		froute = route // rpath
		name = rpath.identifier
		path = ()
		dirq = collections.deque([(froute, path)])
		processed = set()
		typcache = self.source_format_resolution()

		while dirq:
			r, path = dirq.popleft()
			assert r.identifier not in ignore # cache or integration directory
			segment = types.FactorPath.from_sequence(path)

			# Prohibit cycles.
			rdp = None
			for x in r.fs_follow_links():
				rdp = x
			if rdp in processed:
				raise RecursionError(f"filesystem link cycle detected: {r!s} -> {rdp!s}")
			else:
				processed.add(rdp)

			spec = (r // self.FactorDeclarationSignal)
			if r.fs_type() == 'directory' and spec.fs_type() == 'data':
				# Explicit Typed Factor directory.
				cpath = types.FactorPath.from_sequence(path)
				ftype, frefs = structure_factor_declaration(spec.get_text_content())
				sources = self.collect_explicit_sources(typcache, r)

				typref = types.Reference.from_ri('type', ftype)
				resolve = functools.partial(refer, context=(rpath//cpath))
				refs = set(map(resolve, frefs))
				yield (cpath, typref), (refs, sources)

				dirs = files = ()
			else:
				# Not an Explicitly Typed Factor directory.
				dirs, files = r.fs_list('data')

			# Recognize Indirectly Typed Factors.
			ifr = self.indirect_factor_records(typcache, [x for x in files if self.isource(x)])
			for (name, ftype), fstruct in ifr:
				yield ((segment/name), ftype), fstruct

			# Factor Index.
			for x in dirs:
				if x.identifier in ignore:
					continue

				if '.' not in x.identifier:
					dirq.append((x, path + (x.identifier,)))
				else:
					pass

			del dirs, files
