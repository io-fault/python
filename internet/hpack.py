"""
# HTTP/2 header compression tools.

# Provides state machines for managing the dynamic tables needed for connections.
"""
import itertools
import functools

from .data import hpack as data

def huffman_decode(field:bytes,
		h_range=(data.h_start, data.h_stop),
		index=data.huffman_reverse_index,
		bytes=bytes
	):
	"""
	# Decode the byte string using the HPACK huffman code table.

	# [ Invariants ]
		# - `encode(decode(x)) == x`
	"""
	get = index.get
	bits = ''.join(bin(x)[2:].rjust(8, '0') for x in field)

	chars = []
	char = None

	while bits:
		for i in range(*h_range):
			maybe = bits[0:i]
			char = index.get(maybe)
			if char is not None:
				chars.append(char)
				bits = bits[i:]
				break # Next bit string.
		else:
			# Error; no such character. Bad input.
			if bits == (len(bits) * '1'):
				# EOS
				break
			raise ValueError("field contains invalid bit sequence")

	return bytes(chars)

def huffman_encode(field:bytes,
		table=data.huffman_code,
		chain=itertools.chain.from_iterable,
		len=len, int=int
	):
	"""
	# Encode the byte string as using the HPACK huffman code table.

	# [ Invariants ]
		# - `decode(encode(x)) == x`
	"""
	seq = ''.join([table[x] for x in field])
	byte_fields = [seq[y:y+8] for y in range(0, len(seq), 8)]

	last = byte_fields[-1]
	llen = 8 - len(last)
	if llen:
		byte_fields[-1] = (last + ('1' * llen))

	return bytes((int(x, 2) for x in byte_fields))

def encoder(
		hencode=huffman_encode
	):
	"""
	# Encoding state for serializing headers.
	"""
	dindex = {}
	yield None

def decoder(
		hdecode=huffman_decode
	):
	"""
	# Decoding state for loading headers.
	"""
	dindex = {}
	yield None
