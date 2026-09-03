"""
# Python runtime control interfaces.
"""

def signalexit(signo):
	"""
	# Record the &signo and force the process to exit with a default signal
	# after running atexit callbacks and most destructors.
	"""
