"""
# Transport security.
"""
from typing import Protocol
from . import files

class Exception(Exception):
	"""
	# Base exception for all security errors.
	"""

class ProtocolViolation(Exception):
	"""
	# Raised by &Transport when I/O is no longer possible.
	"""

class InvalidCertificate(Exception):
	"""
	# Exception raised to signal certificate related issues.
	"""

class PolicyViolation(InvalidCertificate):
	"""
	# Exceptions signalling that the use of a certificate was probibited.

	# Intended to make the distinction between certificates that were
	# corrupt in some way and those that could not be used due to policy.
	"""

class ExpiredCertificate(PolicyViolation):
	"""
	# Certficate is no longer valid.
	"""

class ForgedCertificate(PolicyViolation):
	"""
	# Certficate signature was not valid.
	"""

class RevokedCertificate(PolicyViolation):
	"""
	# Certficate present in revocation list.
	"""

class UnsuitableCertificate(PolicyViolation):
	"""
	# Certficate cannot be used for the identified purpose.
	"""

class UntrustedCertificate(PolicyViolation):
	"""
	# Certficate issuer could not be found or a part of its chain was marked as untrusted.
	"""

class Certificate(Protocol):
	"""
	# Collection of parameters identifying a peer or authority that are needed
	# to establish secure transports.
	"""

class Context(Protocol):
	"""
	# Collection of certificates and policies used to define the constraints of secure transports.
	"""

	def trust(self, crt:Certificate):
		"""
		# Add the certificate to the set that is used for peer verification.
		"""

class Transport(Protocol):
	"""
	# Secure transport state faciliating encrypted transmission and decrypted reception
	# of information.
	"""

	@classmethod
	def accept(Class, context:Context):
		"""
		# Construct a Transport state instance for accepting a connections.
		"""

	@classmethod
	def connect(Class, context:Context, hostname:bytes):
		"""
		# Construct a Transport state instance for connecting to a server.

		# [ Parameters ]
		# /context/
			# &Context instance defining the contraints of the secured transport.
		# /hostname/
			# The hostname of the service that the connection is being made to.
		"""

	def pending_output(self) -> int:
		"""
		# Number of cipher text bytes available to be writtend from &encipher.
		"""

	def pending_input(self) -> int:
		"""
		# Number of plain text bytes available to be read from &decipher.
		"""

	def encipher(self, plaintext:Iterable[bytes]) -> Sequence[bytes]:
		"""
		# Encrypt the &plaintext elements for transmission.
		"""

	def decipher(self, ciphertext:Iterable[bytes]) -> Sequence[bytes]:
		"""
		# Decrypt the &ciphertext elements for reception.
		"""

	def close(self):
		"""
		# Close the secure transport.
		"""

	@property
	def transmit_closed(self) -> bool:
		"""
		# Whether transmitting is still possible.
		"""

	@property
	def receive_closed(self) -> bool:
		"""
		# Whether receiving is still possible.
		"""

	@property
	def peer_certficiate(self) -> Certificate:
		"""
		# Get the certificate of the peer.
		"""

	@property
	def protocol(self) -> tuple[str, int, int]:
		"""
		# The security protocol employed by the transport.
		"""

	@property
	def application(self) -> bytes:
		"""
		# The currently selected application protocol.
		"""

	@property
	def hostname(self) -> bytes:
		"""
		# The name of the server.
		"""
