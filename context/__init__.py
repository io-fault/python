"""
Fault Context Package Representation

[Executables]
/&.bin.prepare
	Prepare the context package for use. Differs from &..development.bin.prepare by
	performing bootstrapping of context package prior to prepare. No arguments are
	necessary as the location of the package and its name is extracted from containing
	packages.
"""
__factor_type__ = 'project'
context = None
