"""
# Project materialization tools for instantiating polynomial-1 organized factor sets.
"""
import functools
import typing

from types import ModuleType
from dataclasses import dataclass

from ..context.types import Cell
from ..route.types import Segment
from ..text.types import Paragraph
from ..text import render
from ..system import files

from .system import sequence_project_declaration
from . import types

def _ktprotocol(iri):
	return (
		"! CONTEXT:\n\t"
			"/protocol/\n\t\t"
				"&<" + iri + ">\n\n"
	)

# Explicitly Typed Factors
_poly_factor_header = _ktprotocol("http://if.fault.io/project/factor")

def _literal(text):
	return "`" + text.replace("`", "``") + "`"

def _ref(format_id, *text):
	return "&<" + '/'.join(text) + ('#'+format_id if format_id is not None else "") + ">"

def sequence_format_declarations(formats, il='\t', ls='\n'):
	"""
	# factors/polynomial-1 .format serialization
	"""
	for typctx in formats:
		yield str(typctx) + ls

		for typ, ext, fmts, fmtc in formats[typctx]:
			if typctx.endswith('/' + fmtc):
				# factor type implied language class
				yield f"{il}{typ}.{ext} {fmts}{ls}"
			else:
				yield f"{il}{typ}.{ext} {fmts} {fmtc}{ls}"

@dataclass
class Composition(object):
	"""
	# The core data for composing a factor.

	# [ Properties ]
	# /type/
		# The factor type.
	# /requirements/
		# Set of factor references needed for integration.
	# /sources/
		# A sequence of pairs defining the source name and the source content.

		# For polynomial-1, the source name is the extension that will be appended to
		# factor path if sources is a &Cell instance.
	"""
	type: str = None
	requirements: [str] = ()
	sources: typing.Sequence[typing.Tuple[str, typing.Union[str, bytes, files.Path, ModuleType]]] = ()

	@classmethod
	def indirect(Class, extension, source, type=None):
		"""
		# Define an indirectly typed factor's composition.

		# [ Parameters ]
		# /extension/
			# The dot extension that will be appended to the file to identify its type.
		# /source/
			# The data or reference to the data that will be used to initialize the file.
		# /type/
			# An optional factor type string. This is ignored by &plan as this is composing
			# an indirectly typed factor.
		"""
		return Class(type, (), Cell((extension, source)))

	@classmethod
	def explicit(Class, type, requirements, sources):
		"""
		# Define an explicitly typed factor's composition.

		# Equivalent to the default constructor with the exception that &requirements
		# and &sources are copied into a new list.

		# [ Parameters ]
		# /type/
			# The type to be assigned to the factor.
		# /requirements/
			# The set of factors needed for integration.
		# /sources/
			# The iterable producing pairs defining the relative paths and sources.
		"""
		return Class(type, list(requirements), list(sources))

@dataclass
class Parameters(object):
	"""
	# The necessary data for instantiating a project on the local system.

	# [ Properties ]
	# /information/
		# The &types.Information instance defining the project's identity.
	# /formats/
		# The source formats identified by the project.
	# /factors/
		# The set of factors that make up a project; a sequence of factor path-composition pairs.
	# /extensions/
		# Additional project information.
	"""
	information: (types.Information) = None
	formats: (object) = None
	factors: (typing.Sequence[typing.Tuple[types.FactorPath, Composition]]) = ()
	extensions: (types.Extensions) = None

	@classmethod
	def define(Class, information, formats,
			soles=(), sets=(),
			icon:str=None,
			synopsis:str=None,
		):
		"""
		# Create a parameter set for project instantiation applying the proper types
		# to factor entries, and translating factor types to file extensions for defining
		# &soles.

		# [ Parameters ]
		# /information/
			# The project's identification.
		# /formats/
			# The project's source formats.
		# /soles/
			# A sequence of records defining single source factors that should be
			# presented at a path consistent with the factor path.
		# /sets/
			# A sequence of records defining factors with multiple sources.
		# /icon/
			# An IRI identifying the image representing the project.
			# This includes `data` scheme IRIs.
		# /synopsis/
			# A short string describing the project.
		"""

		index = {}
		for typctx in formats:
			for ityp, ext, dialect, language in formats[typctx]:
				ft = '.'.join((typctx, ityp))
				index[ft] = ext

				try:
					shorthand = ft.rsplit('/', 1)[1]
					index[types.factor@shorthand] = ext
				except IndexError:
					pass

		factors = []
		factors.extend([
			(types.factor@path, Composition.indirect(index[typ], src)) # Indirectly Typed Factors
			for path, typ, src in soles
		])

		factors.extend([
			(types.factor@path, Composition(typ, list(sym), list(src))) # Explicitly Typed Factors
			for path, typ, sym, src in sets
		])

		return Class(information, formats, factors, types.Extensions(icon, synopsis))

def plan(info, formats, factors,
		dimensions:typing.Sequence[str]=(),
		protocol='factors/polynomial-1',
		extensions=types.Extensions(None, None),
	):
	"""
	# Generate the filesystem paths paired with the data that should be placed
	# into that file relative to the project directory being materialized.
	"""
	seg = Segment.from_sequence(())

	if info:
		# NOTE: Temporarily swap the identifier to handle dimensions.
		# Relocate this logic into &types.Information as a copy constructor.
		iid = info.identifier
		if dimensions:
			info.identifier += '//' + '/'.join(dimensions)
		pi = sequence_project_declaration(protocol, info)
		info.identifier = iid
		yield (seg/'.project'/'f-identity', pi)

	if extensions.icon:
		yield (seg/'.project'/'icon', extensions.icon.encode('utf-8'))
	if extensions.synopsis:
		yield (seg/'.project'/'synopsis', extensions.synopsis.encode('utf-8'))

	if formats:
		fi = sequence_format_declarations(formats)
		yield (seg/'.project'/'polynomial-1', ''.join(fi))

	for fpath, c in factors:
		if isinstance(c.sources, Cell):
			# sole; indirectly typed factor.
			(ext, data), = c.sources # Only one source in cells.
			p = seg // fpath
			p = p.container / (p.identifier + '.' + ext)
			yield (p, data)
		else:
			# set; explicitly typed factor.
			if c.type == 'factor-index':
				# Special case for allowing directory initialization.
				yield (seg//fpath, None)
			else:
				p = (seg//fpath)
				yield (p/'.factor', f"{c.type}\n" + '\n'.join(c.requirements) + "\n")
				for rpath, data in c.sources:
					yield (p + rpath.split('/'), data)

def materialize(route, plans, encoding='utf-8', isinstance=isinstance):
	"""
	# Create a Project instance using the filesystem API's provided by &route
	# from the instructions produced by the given &plans.

	# ! WARNING:
		# Plan entries referring to files will cause the file content to be loaded entirely into memory.
		# Instantiating projects with large resources may require a side channel in order to achieve
		# reasonable memory usage.

	# [ Parameters ]
	# /route/
		# A, usually filesystem, route to the directory that plan
		# segments will extend into.
	# /plans/
		# An iterable of pairs where the first item is the segment, relative path,
		# and the second is either the data to be stored or a &files.Path instance
		# referring to the data to be stored.
	"""

	for path, data in plans:
		target_file = (route//path)

		if data is None:
			if target_file.fs_type() != 'directory':
				target_file.fs_mkdir()
			continue
		elif isinstance(data, str):
			data = data.encode(encoding)
		elif isinstance(data, bytes):
			pass
		elif isinstance(data, ModuleType):
			data = files.Path.from_absolute(data.__file__).fs_load()
		else:
			# Presume filesystem reference.
			(target_file).fs_link_relative(data) # Symbolic linke.
			continue

		(target_file).fs_init(data)

def instantiate(project:Parameters, route, *dimensions:str):
	"""
	# Materialize the plan of the given &project using the &route as the root directory of the project.

	# [ Parameters ]
	# /project/
		# The set of parameters needed to plan and materialize a project.
	# /route/
		# A route to the root target directory.
	# /dimensions/
		# An optional sequence of strings that will be appended to the project's identifier.
	"""

	return materialize(route, plan(
		project.information,
		project.formats,
		project.factors,
		dimensions=dimensions,
		extensions=project.extensions,
	))
