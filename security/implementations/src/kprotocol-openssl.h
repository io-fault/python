/**
	// SSL_CTX_set_client_cert_cb()
	// SSL_ERROR_WANT_X509_LOOKUP (SSL_get_error return)

	// The OpenSSL folks note a significant limitation of this feature as
	// that the callback functions cannot return a full chain. However,
	// if the chain is pre-configured on the Context, the full chain will be sent.
	// The current implementation of OpenSSL means that a callback selecting
	// the exact chain is... limited.

	// X509_NAMES = SSL_get_client_CA_list(transport_t) - client connection get server (requirements) CA list.
*/
#include <stdio.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <sys/param.h>
#include <sys/socket.h>

#include <openssl/opensslv.h>

#include <openssl/ssl.h>
#include <openssl/tls1.h>
#include <openssl/err.h>
#include <openssl/bio.h>

#include <openssl/x509.h>
#include <openssl/pem.h>
#include <openssl/rsa.h>
#include <openssl/evp.h>

#include <openssl/objects.h>

#define VERIFY_FAILURE 337047686

#ifdef OPENSSL_NO_EVP
	#error fault.security transport context requires openssl with EVP
#endif

#ifndef FAULT_OPENSSL_CIPHERS
	#define FAULT_OPENSSL_CIPHERS "RC4:HIGH:!aNULL:!eNULL:!NULL:!MD5"
#endif

#include <fault/libc.h>
#include <fault/python/environ.h>

#define Transport_GetReadBuffer(tls) (SSL_get_rbio(tls->tls_state))
#define Transport_GetWriteBuffer(tls) (SSL_get_wbio(tls->tls_state))

/*
	// Python Memory Buffers
*/
#define GetPointer(pb) (pb.buf)
#define GetSize(pb) (pb.len)

typedef EVP_PKEY *pki_key_t;

/**
	// Security Context [Cipher/Protocol Parameters]
*/
typedef SSL_CTX *context_t;
#define free_context_t SSL_CTX_free

/**
	// An instance of TLS for facilitating a secure connection.
*/
typedef SSL *transport_t;
#define free_transport_t SSL_free

/**
	// An X509 Certificate.
*/
typedef X509 *certificate_t;
#define free_certificate_t X509_free

static PyObj version_info = NULL, version_str = NULL;

/**
	// Certificate object structure.
*/
struct Certificate {
	PyObject_HEAD
	certificate_t lib_crt;
};
typedef struct Certificate *Certificate;

/**
	// Security context object structure.
*/
struct Context {
	PyObject_HEAD
	context_t tls_context;
	PyObj ctx_queue_type;
};
typedef struct Context *Context;

#define output_buffer_extend(tls, x) PyObject_CallMethod(tls->output_queue, "extend", "(O)", x)
#define output_buffer_append(tls, x) PyObject_CallMethod(tls->output_queue, "append", "O", x)
#define output_buffer_has_content(tls) PyObject_IsTrue(tls->output_queue)
#define output_buffer_initial(tls) PySequence_GetItem(tls->output_queue, 0)
#define output_buffer_pop(tls) PySequence_DelItem(tls->output_queue, 0)

/**
	// TLS connection state.
*/
struct Transport {
	PyObject_HEAD
	Context ctx_object;

	transport_t tls_state;

	/**
		// NULL until inspected then cached until the Transport is terminated.
	*/
	PyObj tls_peer_certificate;
	PyObj output_queue; /* when SSL_write is not possible */
	PyObj recv_closed_cb;
	PyObj send_queued_cb;
};
typedef struct Transport *Transport;

static PyTypeObject KeyType, CertificateType, ContextType, TransportType;

/**
	// Prompting is rather inappropriate from a library;
	// this callback is used throughout the source to manage
	// the encryption key of a certificate or private key.
*/
struct password_parameter {
	char *words;
	Py_ssize_t length;
};

/**
	// Callback used to parameterize the password.
*/
static int
password_parameter(char *buf, int size, int rwflag, void *u)
{
	struct password_parameter *pwp = u;

	strncpy(buf, pwp->words, (size_t) size);
	buf[size] = '\0';
	return((int) pwp->length);
}

#if OPENSSL_VERSION_NUMBER >= 0x1010000fL
	/**
		// TLS methods were changed in 1.1.
	*/
	#define X_TLS_METHODS() X_TLS_METHOD("TLS", TLS)
	#define X_TLS_PROTOCOLS() \
		X_TLS_PROTOCOL(ietf.org, RFC, 0, TLS,  0, 0, TLS)
#else
	#ifndef OPENSSL_NO_SSL3_METHOD
		#define _X_TLS_METHOD_SSLv3 X_TLS_METHOD("SSL-3.0", SSLv3)
	#else
		#define _X_TLS_METHOD_SSLv3
	#endif

	/*
		// OpenSSL V < 1.1 doesn't provide us with an X-Macro of any sort, so hand add as needed.
		// Might have to rely on some probes at some point... =\

		// ORG, TYPE, ID, NAME, VERSION, OPENSSL_FRAGMENT
	*/
	#define X_TLS_PROTOCOLS() \
		X_TLS_PROTOCOL(ietf.org, RFC, 2246, TLS,  1, 0, TLSv1)   \
		X_TLS_PROTOCOL(ietf.org, RFC, 4346, TLS,  1, 1, TLSv1_1) \
		X_TLS_PROTOCOL(ietf.org, RFC, 5246, TLS,  1, 2, TLSv1_2) \
		X_TLS_PROTOCOL(ietf.org, RFC, 6101, SSL,  3, 0, SSLv23)

	/*
		// X_TLS_PROTOCOL(ietf.org, RFC, 8446, TLS,  1, 3, TLSv1_3) \
	*/

	#define X_TLS_METHODS()               \
		X_TLS_METHOD("TLS", TLSv1_2)      \
		X_TLS_METHOD("TLS-1.0", TLSv1)    \
		X_TLS_METHOD("TLS-1.1", TLSv1_1)  \
		X_TLS_METHOD("TLS-1.2", TLSv1_2)  \
		_X_TLS_METHOD_SSLv3 \
		X_TLS_METHOD("compat",  SSLv23)
#endif

#define X_CERTIFICATE_TYPES() \
	X_CERTIFICATE_TYPE(ietf.org, RFC, 5280, X509)

/**
	// TODO
	// Context Cipher List Specification
	// Context Certificate Loading
	// Context Certificate Loading
*/
#define X_TLS_ALGORITHMS() \
	X_TLS_ALGORITHMS(RSA)  \
	X_TLS_ALGORITHMS(DSA)  \
	X_TLS_ALGORITHMS(DH)

#define X_CA_EVENTS()        \
	X_CA_EVENT(CSR, REQUEST) \
	X_CA_EVENT(CRL, REVOKE)

/**
	// Function Set to load Security Elements.
*/
#define X_READ_OPENSSL_OBJECT(TYP, LOCAL_SYM, OPENSSL_CALL) \
static TYP \
LOCAL_SYM(PyObj buf, pem_password_cb *cb, void *cb_data) \
{ \
	Py_buffer pb; \
	TYP element = NULL; \
	BIO *bio; \
	\
	if (PyObject_GetBuffer(buf, &pb, 0)) \
		return(NULL); \
	\
	/* Implicit Read-Only BIO: Py_buffer data is directly referenced. */ \
	bio = BIO_new_mem_buf(GetPointer(pb), GetSize(pb)); \
	if (bio == NULL) \
	{ \
		PyErr_SetString(PyExc_MemoryError, "could not allocate OpenSSL memory for security object"); \
	} \
	else \
	{ \
		element = OPENSSL_CALL(bio, NULL, cb, cb_data); \
		BIO_free(bio); \
	} \
	\
	PyBuffer_Release(&pb); \
	return(element); \
}

/**
	// need a small abstraction
*/
X_READ_OPENSSL_OBJECT(certificate_t, load_pem_certificate, PEM_read_bio_X509)
X_READ_OPENSSL_OBJECT(pki_key_t, load_pem_private_key, PEM_read_bio_PrivateKey)
X_READ_OPENSSL_OBJECT(pki_key_t, load_pem_public_key, PEM_read_bio_PUBKEY)
#undef X_READ_OPENSSL_OBJECT

PyObj PyExc_TransportSecurityError = NULL;

/**
	// OpenSSL uses a per-thread error queue.
*/
static PyObj
openssl_error_pop(void)
{
	PyObj rob;
	int line = -1, flags = 0;
	const char *lib, *func, *reason, *path, *data = NULL, *ldata;
	unsigned long error_code;

	error_code = ERR_get_error_line_data(&path, &line, &data, &flags);

	lib = ERR_lib_error_string(error_code);
	func = ERR_func_error_string(error_code);
	reason = ERR_reason_error_string(error_code);

	if (lib && lib[0] == '\0')
		lib = NULL;

	if (func && func[0] == '\0')
		func = NULL;

	if (reason && reason[0] == '\0')
		reason = NULL;

	if (data && data[0] == '\0')
		ldata = NULL;
	else
		ldata = data;

	if (path && path[0] == '\0')
		path = NULL;

	rob = Py_BuildValue(
		"((sk)(ss)(ss)(ss)(ss)(ss)(si))",
			"code", error_code,
			"library", lib,
			"function", func,
			"reason", reason,
			"data", ldata,
			"path", path,
			"line", line
	);

	return(rob);
}

static PyObj
openssl_error_collect(void)
{
	PyObj stack = NULL;

	stack = PyList_New(0);
	if (stack == NULL)
		return(NULL);

	while (ERR_peek_error() != 0)
	{
		PyObj ie = openssl_error_pop();
		if (ie == NULL)
		{
			Py_DECREF(stack);
			return(NULL);
		}
		PyList_Append(stack, ie);
	}

	return(stack);
}

static void
openssl_error_set(void)
{
	PyObj call = NULL;
	PyObj stack = NULL;
	PyObj val = NULL;

	stack = openssl_error_collect();
	if (stack == NULL)
		return;

	call = PyUnicode_FromString(call);
	if (call == NULL)
		goto error;

	val = PyTuple_Pack(2, call, stack);
	if (val == NULL)
		goto error;

	PyErr_SetObject(PyExc_TransportSecurityError, val);
	error:
	{
		Py_XDECREF(stack);
		Py_XDECREF(val);
		Py_XDECREF(call);
	}
}

static int
library_error(void)
{
	if (ERR_peek_error())
	{
		openssl_error_set();
		return(-1);
	}
	else
		return(0);
}

/**
	// primary &transport_new parts. Normally called by the Context methods.
*/
static Transport
create_tls_state(PyTypeObject *typ, Context ctx)
{
	const static char *mem_err_str = "could not allocate memory BIO for secure Transport";
	Transport tls;
	BIO *rb, *wb;

	tls = (Transport) typ->tp_alloc(typ, 0);
	if (tls == NULL)
		return(NULL);

	tls->recv_closed_cb = NULL;
	tls->send_queued_cb = NULL;

	tls->output_queue = PyObject_CallFunctionObjArgs(ctx->ctx_queue_type, NULL);
	if (tls->output_queue == NULL)
	{
		Py_DECREF(tls);
		return(NULL);
	}

	tls->ctx_object = ctx;
	Py_INCREF(ctx);

	tls->tls_state = SSL_new(ctx->tls_context);
	if (tls->tls_state == NULL)
	{
		library_error();
		Py_DECREF(tls);
		return(tls);
	}

	Py_INCREF(((PyObj) ctx));

	/**
		// I/O buffers for the connection.
		// Unlike SSL_new error handling, be noisy about memory errors.
	*/
	rb = BIO_new(BIO_s_mem());
	wb = BIO_new(BIO_s_mem());

	if (rb == NULL || wb == NULL)
	{
		if (rb)
			BIO_free(rb);
		if (wb)
			BIO_free(wb);

		PyErr_SetString(PyExc_MemoryError, mem_err_str);
		goto error;
	}

	BIO_set_mem_eof_return(rb, -1);
	BIO_set_mem_eof_return(wb, -1);

	SSL_set_bio(tls->tls_state, rb, wb);

	return(tls);

	error:
	{
		Py_DECREF(tls);
		return(NULL);
	}
}

/**
	// Loading certificates from an iterator is common, so
	// a utility macro. Would be a function, but some load ops are macros.
*/
#define CERT_INIT_LOOP(NAME, INITIAL, SUBSEQUENT) \
static int NAME(context_t ctx, PyObj certificates) \
{ \
	PyObj ob, pi; \
	\
	pi = PyObject_GetIter(certificates); \
	if (pi == NULL) \
		return(0); \
	\
	ob = PyIter_Next(pi); \
	if (PyErr_Occurred()) \
		goto error; \
	\
	if (ob != NULL) \
	{ \
		certificate_t cert; \
		\
		cert = load_pem_certificate(ob, NULL, NULL); \
		Py_DECREF(ob); \
		\
		if (cert == NULL) \
		{ \
			if (PyErr_Occurred()) \
				goto error; \
			else \
				goto ierror; \
		} \
		\
		if (!INITIAL(ctx, cert)) \
			goto ierror; \
		\
		while ((ob = PyIter_Next(pi))) \
		{ \
			if (PyErr_Occurred()) \
				goto error; \
			\
			cert = load_pem_certificate(ob, NULL, NULL); \
			Py_DECREF(ob); \
			\
			if (cert == NULL) \
				goto ierror; \
			if (!SUBSEQUENT(ctx, cert)) \
				goto ierror; \
		} \
	} \
	\
	Py_DECREF(pi); \
	return(1); \
	\
	ierror: \
		library_error(); \
	error: \
	{ \
		Py_DECREF(pi); \
		return(0); \
	}\
}

CERT_INIT_LOOP(load_certificate_chain, SSL_CTX_use_certificate, SSL_CTX_add_extra_chain_cert)
CERT_INIT_LOOP(load_client_requirements, SSL_CTX_add_client_CA, SSL_CTX_add_client_CA)

static PyObj
certificate_open(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {
		"path",
		"password",
		NULL
	};

	struct password_parameter pwp = {"", 0};
	char *path = NULL;
	FILE *fp = NULL;
	Certificate cert;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "s|s#", kwlist, &path, &(pwp.words), &(pwp.length)))
		return(NULL);

	cert = (Certificate) subtype->tp_alloc(subtype, 0);
	if (cert == NULL)
		return(NULL);

	fp = fopen(path, "rb");
	if (fp == NULL)
	{
		PyErr_SetFromErrno(PyExc_OSError);
		Py_DECREF(cert);
		return(NULL);
	}

	cert->lib_crt = PEM_read_X509(fp, NULL, password_parameter, &pwp);
	if (cert->lib_crt == NULL)
		goto lib_error;

	return((PyObj) cert);

	lib_error:
		library_error();
	error:
	{
		Py_DECREF(cert);
		return(NULL);
	}
}

static PyMethodDef
certificate_methods[] = {
	{"open", (PyCFunction) certificate_open,
		METH_CLASS|METH_VARARGS|METH_KEYWORDS, PyDoc_STR(
			"Read a certificate directly from the filesystem.\n"
		)
	},

	{NULL,},
};

static PyMemberDef
certificate_members[] = {
	{NULL,},
};

static PyObj
str_from_asn1_string(ASN1_STRING *str)
{
	PyObj rob;
	unsigned char *utf = NULL;
	int len = 0;

	len = ASN1_STRING_to_UTF8(&utf, str);
	rob = PyUnicode_FromStringAndSize((const char *) utf, len);

	OPENSSL_free(utf);

	return(rob);
}

static PyObj
seq_from_names(X509_NAME *n)
{
	X509_NAME_ENTRY *item;

	PyObj rob;
	int i = 0, count;

	rob = PyList_New(0);
	if (rob == NULL)
		return(NULL);

	count = X509_NAME_entry_count(n);
	while (i < count)
	{
		PyObj val, robi = NULL;
		ASN1_OBJECT *iob;
		int nid;
		const char *name;

		item = X509_NAME_get_entry(n, i);
		iob = X509_NAME_ENTRY_get_object(item);

		val = str_from_asn1_string(X509_NAME_ENTRY_get_data(item));
		if (val == NULL)
		{
			Py_DECREF(rob);
			return(NULL);
		}

		nid = OBJ_obj2nid(iob);
		name = OBJ_nid2ln(nid);

		robi = Py_BuildValue("(sO)", name, val);

		if (robi == NULL || PyList_Append(rob, robi))
		{
			Py_DECREF(rob);
			return(NULL);
		}

		++i;
	}

	return(rob);
}

static PyObj
str_from_asn1_time(ASN1_TIME *t)
{
	PyObj rob;
	ASN1_GENERALIZEDTIME *gt;

	/*
		// The other variants are strings as well...
		// The UTCTIME strings omit the century and
		// millennium parts of the year.
	*/

	gt = ASN1_TIME_to_generalizedtime(t, NULL);
	rob = PyUnicode_FromStringAndSize((const char *) ASN1_STRING_get0_data(gt), ASN1_STRING_length(gt));
	ASN1_STRING_free(gt);

	return(rob);
}

static PyObj
str_from_nid(int n)
{
	return(PyUnicode_FromString(OBJ_nid2ln(n)));
}

static PyObj
long_from_asn1_integer(ASN1_INTEGER *i)
{
	return(PyLong_FromLong(ASN1_INTEGER_get(i)));
}

#define CERTIFICATE_PROPERTIES() \
	CERT_PROPERTY(not_before_string, \
		"The 'notBefore' field as a string.", X509_get_notBefore, str_from_asn1_time) \
	CERT_PROPERTY(not_after_string, \
		"The 'notAfter' field as a string.", X509_get_notAfter, str_from_asn1_time) \
	CERT_PROPERTY(signature_type, \
		"The type of signature used to sign the key.", X509_get_signature_type, str_from_nid) \
	CERT_PROPERTY(subject, \
		"The subject data of the cerficate.", X509_get_subject_name, seq_from_names) \
	CERT_PROPERTY(issuer, \
		"The issuer data of the cerficate.", X509_get_issuer_name, seq_from_names) \
	CERT_PROPERTY(version, \
		"The Format Version", X509_get_version, PyLong_FromLong) \
	CERT_PROPERTY(serial, \
		"The serial number field", X509_get_serialNumber, long_from_asn1_integer)

#define CERT_PROPERTY(NAME, DOC, GET, CONVERT) \
	static PyObj certificate_get_##NAME(PyObj crt, void *p) \
	{ \
		certificate_t lib_crt = ((Certificate) crt)->lib_crt; \
		return(CONVERT(GET(lib_crt))); \
	} \

	CERTIFICATE_PROPERTIES()
#undef CERT_PROPERTY

static PyObj
certificate_get_type(PyObj self, void *p)
{
	return(PyUnicode_FromString("x509"));
}

static PyGetSetDef certificate_getset[] = {
	#define CERT_PROPERTY(NAME, DOC, UNUSED1, UNUSED2) \
		{#NAME, certificate_get_##NAME, NULL, PyDoc_STR(DOC)},

		CERTIFICATE_PROPERTIES()
	#undef CERT_PROPERTY

	{"type",
		certificate_get_type, NULL,
		PyDoc_STR("certificate type; always X509."),
	},
	{NULL,},
};

static void
certificate_dealloc(PyObj self)
{
	Certificate cert = (Certificate) self;
	X509_free(cert->lib_crt);
	Py_TYPE(self)->tp_free(self);
}

static PyObj
certificate_repr(PyObj self)
{
	Certificate cert = (Certificate) self;
	PyObj rob, sn_ob;
	BIO *b;
	char *ptr;
	long size;
	X509_NAME *sn;

	sn = X509_get_subject_name(cert->lib_crt);

	b = BIO_new(BIO_s_mem());

	X509_NAME_print(b, sn, 0);

	size = BIO_get_mem_data(b, &ptr);

	sn_ob = Py_BuildValue("s#", ptr, size);
	rob = PyUnicode_FromFormat("<%s [%U] %p>", Py_TYPE(self)->tp_name, sn_ob, cert);

	BIO_free(b);

	return(rob);
}

static PyObj
certificate_str(PyObj self)
{
	Certificate cert = (Certificate) self;
	PyObj rob;
	BIO *b;
	char *ptr;
	long size;

	b = BIO_new(BIO_s_mem());
	X509_print(b, cert->lib_crt);

	size = BIO_get_mem_data(b, &ptr);

	rob = Py_BuildValue("s#", ptr, size);

	BIO_free(b);

	return(rob);
}

static PyObj
certificate_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {
		"pem",
		"password",
		NULL,
	};
	struct password_parameter pwp = {"", 0};

	PyObj pem;
	Certificate cert;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "O|s#", kwlist,
			&pem,
			&(pwp.words), &(pwp.length)
		))
		return(NULL);

	cert = (Certificate) subtype->tp_alloc(subtype, 0);
	if (cert == NULL)
		return(NULL);

	cert->lib_crt = load_pem_certificate(pem, password_parameter, &pwp);
	if (cert->lib_crt == NULL)
		goto lib_error;

	return((PyObj) cert);

	lib_error:
		library_error();
	error:
	{
		Py_XDECREF(cert);
		return(NULL);
	}
}

PyDoc_STRVAR(certificate_doc, "OpenSSL X509 Certificate Objects");

static PyTypeObject
CertificateType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	PYTHON_MODULE_PATH("Certificate"), /* tp_name */
	sizeof(struct Certificate),        /* tp_basicsize */
	0,                                 /* tp_itemsize */
	certificate_dealloc,               /* tp_dealloc */
	NULL,                              /* tp_print */
	NULL,                              /* tp_getattr */
	NULL,                              /* tp_setattr */
	NULL,                              /* tp_compare */
	certificate_repr,                  /* tp_repr */
	NULL,                              /* tp_as_number */
	NULL,                              /* tp_as_sequence */
	NULL,                              /* tp_as_mapping */
	NULL,                              /* tp_hash */
	NULL,                              /* tp_call */
	certificate_str,                   /* tp_str */
	NULL,                              /* tp_getattro */
	NULL,                              /* tp_setattro */
	NULL,                              /* tp_as_buffer */
	Py_TPFLAGS_BASETYPE|
	Py_TPFLAGS_DEFAULT,                /* tp_flags */
	certificate_doc,                   /* tp_doc */
	NULL,                              /* tp_traverse */
	NULL,                              /* tp_clear */
	NULL,                              /* tp_richcompare */
	0,                                 /* tp_weaklistoffset */
	NULL,                              /* tp_iter */
	NULL,                              /* tp_iternext */
	certificate_methods,               /* tp_methods */
	certificate_members,               /* tp_members */
	certificate_getset,                /* tp_getset */
	NULL,                              /* tp_base */
	NULL,                              /* tp_dict */
	NULL,                              /* tp_descr_get */
	NULL,                              /* tp_descr_set */
	0,                                 /* tp_dictoffset */
	NULL,                              /* tp_init */
	NULL,                              /* tp_alloc */
	certificate_new,                   /* tp_new */
};

static PyObj
context_accept(PyObj self)
{
	Context ctx = (Context) self;
	Transport tls;
	int r;

	tls = create_tls_state(&TransportType, ctx);
	if (tls == NULL)
		return(NULL);

	SSL_set_accept_state(tls->tls_state);

	if (SSL_do_handshake(tls->tls_state) != 0 && library_error())
		goto error;

	return((PyObj) tls);

	error:
	{
		Py_DECREF((PyObj) tls);
		return(NULL);
	}
}

static int
_transport_set_hostname(Transport tls, PyObj hostname)
{
	char *name = NULL;
	Py_ssize_t size = 0;
	int err;

	/* no hostname */
	if (hostname == Py_None)
		return(0);

	if (PyBytes_AsStringAndSize(hostname, &name, &size))
		return(-1);

	err = SSL_set_tlsext_host_name(tls->tls_state, (const char *) name);
	if (err != 1)
	{
		library_error();
		return(-1);
	}

	return(0);
}

static PyObj
context_connect(PyObj self, PyObj hostname)
{
	Context ctx = (Context) self;
	Transport tls;
	int r;

	tls = create_tls_state(&TransportType, ctx);
	if (tls == NULL)
		return(NULL);

	if (_transport_set_hostname(tls, hostname))
		goto error;

	SSL_set_connect_state(tls->tls_state);

	if (SSL_do_handshake(tls->tls_state) != 0 && library_error())
		goto error;

	return((PyObj) tls);

	error:
	{
		Py_DECREF((PyObj) tls);
		return(NULL);
	}
}

static PyObj
context_reset_sessions(PyObj self, PyObj args)
{
	Context ctx = (Context) self;
	long t = 0;

	if (!PyArg_ParseTuple(args, "l", &t))
		return(NULL);

	SSL_CTX_flush_sessions(ctx->tls_context, t);

	Py_RETURN_NONE;
}

static PyMethodDef
context_methods[] = {
	{"accept", (PyCFunction) context_accept,
		METH_NOARGS, PyDoc_STR(
			"Allocate a server TLS `Transport` instance for "
			"secure transmission of data associated with the Context."
		)
	},

	{"connect", (PyCFunction) context_connect,
		METH_O, PyDoc_STR(
			"Allocate a client TLS `Transport` instance for "
			"secure transmission of data associated with the Context."
		)
	},

	{"reset", (PyCFunction) context_reset_sessions,
		METH_VARARGS, PyDoc_STR(
			"Remove the sessions from the context that have expired "
			"according to the given time parameter."
		)
	},

	{NULL,},
};

static PyMemberDef
context_members[] = {
	{NULL,},
};

static int
context_clear(PyObj self)
{
	Context ctx = (Context) self;

	Py_XDECREF(ctx->ctx_queue_type);
	ctx->ctx_queue_type = NULL;

	return(0);
}

static int
context_traverse(PyObj self, visitproc visit, void *arg)
{
	Context ctx = (Context) self;

	Py_VISIT(ctx->ctx_queue_type);
	return(0);
}

static void
context_dealloc(PyObj self)
{
	Context ctx = (Context) self;

	if (ctx->tls_context)
		SSL_CTX_free(ctx->tls_context);

	context_clear(self);
	Py_TYPE(self)->tp_free(self);
}

static PyObj
context_repr(PyObj self)
{
	Context ctx = (Context) self;
	PyObj rob;

	rob = PyUnicode_FromFormat("<%s %p>", Py_TYPE(self)->tp_name, ctx);
	return(rob);
}

static PyObj
context_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {
		"key",
		"password",
		"certificates",
		"requirements",
		"ciphers",
		NULL,
	};

	struct password_parameter pwp = {"", 0};

	Context ctx;

	PyObj key_ob = NULL;
	PyObj certificates = NULL; /* iterable */
	PyObj requirements = NULL; /* iterable */

	char *ciphers = FAULT_OPENSSL_CIPHERS;

	if (!PyArg_ParseTupleAndKeywords(args, kw,
		"|Os#OOss", kwlist,
		&key_ob,
		&(pwp.words), &(pwp.length),
		&certificates,
		&requirements,
		&ciphers
	))
		return(NULL);

	ctx = (Context) subtype->tp_alloc(subtype, 0);
	if (ctx == NULL)
		return(NULL);

	/*
		// For SSL_write buffer. Not many contexts should be created, so cache on instance.
	*/
	{
		PyObj qmod;
		qmod = PyImport_ImportModule("collections");
		if (qmod == NULL)
			goto error;

		ctx->ctx_queue_type = PyObject_GetAttrString(qmod, "deque");
		Py_DECREF(qmod);

		if (ctx->ctx_queue_type == NULL)
			goto error;
	}

	/*
		// The key is checked and loaded later.
	*/
	ctx->tls_context = SSL_CTX_new(TLS_method());

	if (ctx->tls_context == NULL)
	{
		/* XXX: check for openssl failure */
		goto ierror;
	}
	else
	{
		/*
			// Context initialization.
		*/
		SSL_CTX_set_mode(ctx->tls_context, SSL_MODE_RELEASE_BUFFERS|SSL_MODE_AUTO_RETRY);
		SSL_CTX_set_read_ahead(ctx->tls_context, 1);
	}

	SSL_CTX_load_verify_locations(ctx->tls_context,
		CONTEXT_LOCATION "/net/ca-bundle.crt",
		CONTEXT_LOCATION "/net/certificates");
	SSL_CTX_set_verify(ctx->tls_context, ADAPTER_VERIFY, NULL);

	#ifdef SSL_OP_NO_SSLv2
		SSL_CTX_set_options(ctx->tls_context, SSL_OP_NO_SSLv2);
	#endif

	#ifdef SSL_OP_NO_SSLv3
		SSL_CTX_set_options(ctx->tls_context, SSL_OP_NO_SSLv3);
	#endif

	#ifdef SSL_OP_NO_TLSv1
		SSL_CTX_set_options(ctx->tls_context, SSL_OP_NO_TLSv1);
	#endif

	#ifdef SSL_OP_NO_CLIENT_RENEGOTIATION
		SSL_CTX_set_options(ctx->tls_context, SSL_OP_NO_CLIENT_RENEGOTIATION);
	#endif

	#ifdef SSL_MODE_RELEASE_BUFFERS
		SSL_CTX_set_mode(ctx->tls_context, SSL_MODE_RELEASE_BUFFERS);
	#endif

	#ifdef SSL_MODE_NO_AUTO_CHAIN
		SSL_CTX_set_mode(ctx->tls_context, SSL_MODE_NO_AUTO_CHAIN);
	#endif

	if (!SSL_CTX_set_cipher_list(ctx->tls_context, ciphers))
		goto ierror;

	/*
		// Load certificates.
	*/
	if (certificates != NULL)
	{
		if (!load_certificate_chain(ctx->tls_context, certificates))
			goto ierror;
	}

	if (requirements != NULL)
	{
		if (!load_client_requirements(ctx->tls_context, requirements))
			goto ierror;
	}

	if (key_ob != NULL)
	{
		pki_key_t key;

		key = load_pem_private_key(key_ob, password_parameter, &pwp);
		if (key == NULL)
		{
			goto ierror;
		}

		if (SSL_CTX_use_PrivateKey(ctx->tls_context, key)
				&& SSL_CTX_check_private_key(ctx->tls_context))
			;
		else
		{
			goto ierror;
		}
	}

	return((PyObj) ctx);

	ierror:
	{
		library_error();
	}

	error:
	{
		Py_XDECREF(ctx);
		return(NULL);
	}
}

PyDoc_STRVAR(context_doc, "OpenSSL transport security context.");
static PyTypeObject
ContextType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	PYTHON_MODULE_PATH("Context"),   /* tp_name */
	sizeof(struct Context),          /* tp_basicsize */
	0,                               /* tp_itemsize */
	context_dealloc,                 /* tp_dealloc */
	NULL,                            /* tp_print */
	NULL,                            /* tp_getattr */
	NULL,                            /* tp_setattr */
	NULL,                            /* tp_compare */
	context_repr,                    /* tp_repr */
	NULL,                            /* tp_as_number */
	NULL,                            /* tp_as_sequence */
	NULL,                            /* tp_as_mapping */
	NULL,                            /* tp_hash */
	NULL,                            /* tp_call */
	NULL,                            /* tp_str */
	NULL,                            /* tp_getattro */
	NULL,                            /* tp_setattro */
	NULL,                            /* tp_as_buffer */
	Py_TPFLAGS_BASETYPE|
	Py_TPFLAGS_HAVE_GC|
	Py_TPFLAGS_DEFAULT,              /* tp_flags */
	context_doc,                     /* tp_doc */
	context_traverse,                /* tp_traverse */
	context_clear,                   /* tp_clear */
	NULL,                            /* tp_richcompare */
	0,                               /* tp_weaklistoffset */
	NULL,                            /* tp_iter */
	NULL,                            /* tp_iternext */
	context_methods,                 /* tp_methods */
	context_members,                 /* tp_members */
	NULL,                            /* tp_getset */
	NULL,                            /* tp_base */
	NULL,                            /* tp_dict */
	NULL,                            /* tp_descr_get */
	NULL,                            /* tp_descr_set */
	0,                               /* tp_dictoffset */
	NULL,                            /* tp_init */
	NULL,                            /* tp_alloc */
	context_new,                     /* tp_new */
};

/**
	// extract the status of the TLS connection
*/
static PyObj
transport_status(PyObj self)
{
	Transport tls = (Transport) self;
	PyObj rob;

	rob = Py_BuildValue("(sssi)",
		SSL_get_version(tls->tls_state),
		SSL_state_string(tls->tls_state),
		SSL_state_string_long(tls->tls_state),
		SSL_want(tls->tls_state)
	);

	return(rob);
}

/**
	// SSL_write the buffer entries.
*/
static int
transport_flush(Transport tls)
{
	int xfer, r;
	Py_buffer pb;
	PyObj cwb;

	cwb = output_buffer_initial(tls);
	if (cwb == NULL)
		return(-1);

	if (PyObject_GetBuffer(cwb, &pb, PyBUF_SIMPLE))
	{
		Py_DECREF(cwb);
		output_buffer_pop(tls);
		return(-1);
	}

	if (GetSize(pb))
		xfer = SSL_write(tls->tls_state, GetPointer(pb), GetSize(pb));
	else
		/* zero buffer size, pop it */
		xfer = 1;

	if (xfer < 1)
	{
		if (library_error())
			r = -2;
		else
		{
			switch (SSL_get_error(tls->tls_state, xfer))
			{
				default:
					r = 0;
				break;
			}
		}
	}
	else
	{
		r = output_buffer_pop(tls);
		if (r >= 0)
		{
			r = 1; /* processed something */
		}
	}

	Py_DECREF(cwb);
	PyBuffer_Release(&pb);

	return(r); /* r < 0 on python error */
}

/**
	// EOF signals.
*/
static PyObj
transport_enciphered_read_eof(PyObj self, PyObj buffer)
{
	Transport tls = (Transport) self;
	BIO_set_mem_eof_return(Transport_GetReadBuffer(tls), 0);
	Py_RETURN_NONE;
}

static PyObj
transport_enciphered_write_eof(PyObj self, PyObj buffer)
{
	Transport tls = (Transport) self;
	BIO_set_mem_eof_return(Transport_GetWriteBuffer(tls), 0);
	Py_RETURN_NONE;
}

#define DEFAULT_READ_SIZE (1024 * 4)

/**
	// Write enciphered protocol data from the remote end into the transport.
	// Either for deciphered reads or for internal protocol management.
	// It is possible that empty buffer sequences return deciphered data.
*/
static PyObj
transport_decipher(PyObj self, PyObj buffer_sequence)
{
	Transport tls = (Transport) self;
	Py_buffer pb;
	int xfer;
	PyObj rob, bufobj;

	/**
		// No need for a queue on decipher as the BIO will function
		// as our buffer. SSL_write will fail during negotiation, but BIO_write won't.
	*/
	PyLoop_ForEach(buffer_sequence, &bufobj)
	{
		Py_ssize_t bsize;

		if (PyObject_GetBuffer(bufobj, &pb, PyBUF_SIMPLE))
			break;

		bsize = GetSize(pb);

		/* BIO_write always appends for memory BIOs */
		xfer = BIO_write(Transport_GetReadBuffer(tls), GetPointer(pb), bsize);
		PyBuffer_Release(&pb);

		if (xfer != bsize && bsize > 0)
		{
			/* http://www.openssl.org/docs/manmaster/crypto/BIO_write.html */
			/* unsupported BIO operation shouldn't happen. */
			assert(xfer != -2);

			/* XXX: improve BIO_write failure */
			PyErr_SetString(PyExc_MemoryError, "ciphertext truncated in buffer");
			break;
		}
	}
	PyLoop_CatchError(buffer_sequence)
	{
		/* XXX: note Transport as broken? */
		return(NULL);
	}
	PyLoop_End()

	rob = PyList_New(0);
	if (rob == NULL)
		return(NULL);

	xfer = 0;
	do
	{
		char *bufptr;
		PyObj buffer;

		buffer = PyByteArray_FromObject(NULL);
		if (buffer == NULL)
		{
			Py_DECREF(rob);
			return(NULL);
		}

		if (PyByteArray_Resize(buffer, DEFAULT_READ_SIZE))
		{
			Py_DECREF(buffer);
			Py_DECREF(rob);
			return(NULL);
		}

		/* Only reference to this bytearray, so don't bother with buffer protocol. */
		bufptr = PyByteArray_AS_STRING(buffer);

		xfer = SSL_read(tls->tls_state, bufptr, DEFAULT_READ_SIZE);
		if (xfer < 1 && library_error())
		{
			Py_DECREF(buffer);
			break;
		}
		else if (xfer > 0)
		{
			if (PyByteArray_Resize(buffer, MAX(0, xfer)) || PyList_Append(rob, buffer))
			{
				Py_DECREF(buffer);
				Py_DECREF(rob);
				return(NULL);
			}
		}
		else
		{
			/* Check for termination. */
			if (tls->recv_closed_cb != NULL && SSL_get_shutdown(tls->tls_state) & SSL_RECEIVED_SHUTDOWN)
			{
				PyObj cbout;

				cbout = PyObject_CallFunction(tls->recv_closed_cb, NULL);
				Py_DECREF(tls->recv_closed_cb);
				tls->recv_closed_cb = NULL;

				if (cbout)
					Py_DECREF(cbout);
				else
					PyErr_WriteUnraisable(NULL);
			}

		}

		Py_DECREF(buffer); /* New reference owned by return list or error */
	}
	while (xfer == DEFAULT_READ_SIZE);

	/**
		// Check if deciphering caused any writes and drain the transmit side
		// if any callbacks are available.
	*/
	if (BIO_ctrl_pending(Transport_GetWriteBuffer(tls))
		|| SSL_get_error(tls->tls_state, xfer) == SSL_ERROR_WANT_WRITE
		|| output_buffer_has_content(tls) == 1)
	{
		if (tls->send_queued_cb != NULL)
		{
			PyObj cbout;

			cbout = PyObject_CallFunction(tls->send_queued_cb, NULL);

			if (cbout)
				Py_DECREF(cbout);
			else
				PyErr_WriteUnraisable(NULL);
		}
	}

	return(rob);
}

/**
	// Write plaintext data to be enciphered and return the ciphertext to be written
	// to the remote end.
*/
static PyObj
transport_encipher(PyObj self, PyObj buffer_sequence)
{
	Transport tls = (Transport) self;
	int xfer;
	int flush_result;
	char wrote = 0;
	Py_ssize_t queued = 0;
	PyObj rob, r; /* used to check deque operation results */
	BIO *wb = Transport_GetWriteBuffer(tls);

	/* Extend queue unconditionally */
	r = output_buffer_extend(tls, buffer_sequence);
	if (r == NULL)
		return(NULL);

	/* Move buffers out of queue and into the Transport. */
	flushing:
	{
		switch(output_buffer_has_content(tls))
		{
			case 0:
				/* empty output_queue, perform BIO reads */
			break;

			case 1:
				flush_result = transport_flush(tls);
				if (flush_result > 0)
					goto flushing; /* continue */
				else if (flush_result == -2)
				{
					/* protocol error assigned to transport */
					;
				}
				else if (flush_result < 0)
				{
					/* PyErr_Occurred() */
					return(NULL);
				}
				else
				{
					/* empty buffer */
				}
			break;

			default:
				/* output_buffer_has_content error */
				return(NULL);
			break;
		}
	}

	#if !(FV_INJECTIONS())
		/**
			// Avoid early return during tests.
		*/
		if (BIO_ctrl_pending(wb) == 0)
		{
			return(PyTuple_New(0));
		}
	#endif

	rob = PyList_New(0);
	if (rob == NULL)
		return(NULL);

	xfer = 0;
	do
	{
		char *bufptr = 0;
		PyObj buffer;

		buffer = PyByteArray_FromObject(NULL);
		if (buffer == NULL)
			return(NULL);

		if (PyByteArray_Resize(buffer, DEFAULT_READ_SIZE))
		{
			Py_DECREF(buffer);
			Py_DECREF(rob);
			return(NULL);
		}

		/* Only reference to this bytearray, so don't bother with buffer protocol. */
		bufptr = PyByteArray_AS_STRING(buffer);

		xfer = BIO_read(wb, bufptr, DEFAULT_READ_SIZE);
		if (xfer < 0)
		{
			assert(xfer != -2); /* Not Implemented? Memory BIOs implement read */
		}
		else
		{
			if (PyByteArray_Resize(buffer, MAX(0, xfer)) || PyList_Append(rob, buffer))
			{
				/* failed to resize and append */

				Py_DECREF(buffer);
				Py_DECREF(rob);
				return(NULL);
			}
		}

		Py_DECREF(buffer); /* New reference owned by rob; drop our reference. */
	}
	while (xfer == DEFAULT_READ_SIZE);

	return(rob);
}

static PyObj
transport_leak(PyObj self)
{
	Transport tls = (Transport) self;

	SSL_set_quiet_shutdown(tls->tls_state, 1);
	Py_RETURN_NONE;
}

static PyObj
transport_pending_output(PyObj self)
{
	Transport tls = (Transport) self;
	return(PyLong_FromLong(BIO_pending(Transport_GetWriteBuffer(tls))));
}

static PyObj
transport_pending_input(PyObj self)
{
	Transport tls = (Transport) self;
	return(PyLong_FromLong(SSL_pending(tls->tls_state)));
}

/**
	// Close writes.
*/
static PyObj
transport_close_output(PyObj self)
{
	Transport tls = (Transport) self;

	if (SSL_in_init(tls->tls_state))
	{
		Py_INCREF(Py_False);
		return(Py_False);
	}

	if (SSL_shutdown(tls->tls_state) < 0)
	{
		if (library_error())
			Py_RETURN_NONE;
	}

	Py_INCREF(Py_True);
	return(Py_True);
}

static PyObj
transport_connect_transmit_ready(PyObj self, PyObj ob)
{
	Transport tls = (Transport) self;
	Py_XDECREF(tls->send_queued_cb);

	if (ob == Py_None)
		tls->send_queued_cb = NULL;
	else
	{
		tls->send_queued_cb = ob;
		Py_INCREF(ob);
	}

	Py_RETURN_NONE;
}

static PyObj
transport_connect_receive_closed(PyObj self, PyObj ob)
{
	Transport tls = (Transport) self;
	Py_XDECREF(tls->recv_closed_cb);

	if (ob == Py_None)
		tls->recv_closed_cb = NULL;
	else
	{
		tls->recv_closed_cb = ob;
		Py_INCREF(ob);
	}

	Py_RETURN_NONE;
}

static PyMethodDef
transport_methods[] = {
	{"status", (PyCFunction) transport_status,
		METH_NOARGS, PyDoc_STR(
			"Get the transport's status."
		)
	},

	{"leak", (PyCFunction) transport_leak,
		METH_NOARGS, PyDoc_STR(
			"Inhibit close from being transmitted to the peer."
		)
	},

	{"pending_input", (PyCFunction) transport_pending_input,
		METH_NOARGS, PyDoc_STR(
			"Whether or not the Transport can read data."
		)
	},

	{"pending_output", (PyCFunction) transport_pending_output,
		METH_NOARGS, PyDoc_STR(
			"Whether or not the Transport needs to write data."
		)
	},

	{"close", (PyCFunction) transport_close_output,
		METH_NOARGS, PyDoc_STR("Initiate shutdown closing output.")
	},

	{"encipher", (PyCFunction) transport_encipher,
		METH_O, PyDoc_STR(
			"Encrypt the given plaintext buffers and return the ciphertext buffers."
		)
	},

	{"decipher", (PyCFunction) transport_decipher,
		METH_O, PyDoc_STR(
			"Decrypt the ciphertext buffers into a sequence plaintext buffers."
		)
	},

	{"connect_transmit_ready", (PyCFunction) transport_connect_transmit_ready,
		METH_O, PyDoc_STR("Set callback to be used when an operation causes transmit data.")},

	{"connect_receive_closed", (PyCFunction) transport_connect_receive_closed,
		METH_O, PyDoc_STR("Set callback to be used when peer shutdown has been received.")},

	{NULL},
};

static PyMemberDef
transport_members[] = {
	{"output_queue", T_OBJECT,
		offsetof(struct Transport, output_queue), READONLY,
		PyDoc_STR("Currently enqueued writes.")
	},

	{NULL},
};

#if OPENSSL_VERSION_NUMBER < 0x1000200fL
	#define SSL_get0_alpn_selected(X, strptr, intptr) { *intptr = 0; }
#endif

/**
	// Get the currently selected application layer protocol.
*/
static PyObj
transport_get_application(PyObj self, void *_)
{
	Transport tls = (Transport) self;
	PyObj rob = NULL;
	const unsigned char *data = NULL;
	unsigned int l = 0;

	SSL_get0_alpn_selected(tls->tls_state, &data, &l);
	if (l > 0)
	{
		rob = PyBytes_FromStringAndSize((const char *) data, l);
	}
	else
	{
		rob = Py_None;
		Py_INCREF(rob);
	}

	return(rob);
}

static PyObj
transport_get_hostname(PyObj self, void *_)
{
	Transport tls = (Transport) self;
	PyObj rob = NULL;
	const char *name = NULL;
	unsigned int l = 0;

	name = SSL_get_servername(tls->tls_state, TLSEXT_NAMETYPE_host_name);
	if (name != NULL)
	{
		rob = PyBytes_FromStringAndSize((const char *) name, strlen(name));
	}
	else
	{
		rob = Py_None;
		Py_INCREF(rob);
	}

	return(rob);
}

/**
	// Get the *TLS* protocol being used by the transport.
*/
static PyObj
transport_get_protocol(PyObj self, void *_)
{
	Transport tls = (Transport) self;
	PyObj rob = NULL;
	const SSL_METHOD *p = SSL_get_ssl_method(tls->tls_state);

	#define X_TLS_PROTOCOL(ORG, STD, SID, NAME, MAJOR_VERSION, MINOR_VERSION, OPENSSL_METHOD) \
		if (p == (OPENSSL_METHOD##_method()) \
			|| p == (OPENSSL_METHOD##_client_method()) \
			|| p == (OPENSSL_METHOD##_server_method)()) \
			rob = Py_BuildValue("sii", #NAME, MAJOR_VERSION, MINOR_VERSION); \
		else
		X_TLS_PROTOCOLS()

		/* final else without an if */
		{
			rob = Py_None;
			Py_INCREF(rob);
		}
	#undef X_TLS_PROTOCOL

	return(rob);
}

static PyObj
transport_get_standard(PyObj self, void *_)
{
	Transport tls = (Transport) self;
	PyObj rob = NULL;
	const SSL_METHOD *p = SSL_get_ssl_method(tls->tls_state);

	#define X_TLS_PROTOCOL(ORG, STD, SID, NAME, MAJOR_VERSION, MINOR_VERSION, OPENSSL_METHOD) \
		if (p == (OPENSSL_METHOD##_method()) \
			|| p == (OPENSSL_METHOD##_client_method()) \
			|| p == (OPENSSL_METHOD##_server_method)()) \
			rob = Py_BuildValue("ssi", #ORG, #STD, SID); \
		else
		X_TLS_PROTOCOLS()

		/* final else without an if */
		{
			rob = Py_None;
			Py_INCREF(rob);
		}
	#undef X_TLS_PROTOCOL

	return(rob);
}

static PyObj
transport_get_peer_certificate(PyObj self, void *_)
{
	Transport tls = (Transport) self;

	if (tls->tls_peer_certificate != NULL)
	{
		Py_INCREF(tls->tls_peer_certificate);
		return(tls->tls_peer_certificate);
	}
	else
	{
		Certificate crt;
		certificate_t c;

		c = SSL_get_peer_certificate(tls->tls_state);
		if (c != NULL)
		{
			crt = (Certificate) CertificateType.tp_alloc(&CertificateType, 0);

			if (crt == NULL)
				free_certificate_t(c);
			else
				crt->lib_crt = c;

			return((PyObj) crt);
		}
	}

	Py_RETURN_NONE;
}

static PyObj
transport_get_receive_closed(PyObj self, void *_)
{
	Transport tls = (Transport) self;

	if (SSL_get_shutdown(tls->tls_state) & SSL_RECEIVED_SHUTDOWN)
	{
		Py_INCREF(Py_True);
		return(Py_True);
	}

	Py_INCREF(Py_False);
	return(Py_False);
}

static PyObj
transport_get_transmit_closed(PyObj self, void *_)
{
	Transport tls = (Transport) self;

	if (SSL_get_shutdown(tls->tls_state) & SSL_SENT_SHUTDOWN)
	{
		Py_INCREF(Py_True);
		return(Py_True);
	}

	Py_INCREF(Py_False);
	return(Py_False);
}

const char *
violation(long vr)
{
	switch (vr)
	{
		case X509_V_ERR_CERT_NOT_YET_VALID:
			return("not-yet-valid");
		break;

		case X509_V_ERR_CERT_HAS_EXPIRED:
			return("expired");
		break;

		case X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY:
		case X509_V_ERR_SELF_SIGNED_CERT_IN_CHAIN:
		case X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT:
		case X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT:
		case X509_V_ERR_CERT_UNTRUSTED:
			return("untrusted");
		break;

		case X509_V_ERR_CERT_REVOKED:
			return("revoked");
		break;

		case X509_V_ERR_CERT_REJECTED:
			return("rejected");
		break;

		case X509_V_ERR_CERT_SIGNATURE_FAILURE:
			return("signature-mismatch");
		break;

		case X509_V_ERR_ERROR_IN_CERT_NOT_BEFORE_FIELD:
		case X509_V_ERR_ERROR_IN_CERT_NOT_AFTER_FIELD:
		default:
			return("invalid");
		break;
	}
}

static PyObj
transport_get_violation(PyObj self, void *_)
{
	Transport tls = (Transport) self;
	long vr;
	const char *x;

	vr = SSL_get_verify_result(tls->tls_state);
	if (vr == X509_V_OK)
	{
		Py_RETURN_NONE;
	}

	return(Py_BuildValue("ss", violation(vr), X509_verify_cert_error_string(vr)));
}

static PyGetSetDef transport_getset[] = {
	{"application", transport_get_application, NULL,
		PyDoc_STR(
			"The application protocol specified by the Transport as a bytes instance."
		),
		NULL,
	},

	{"hostname", transport_get_hostname, NULL,
		PyDoc_STR(
			"Get the hostname used by the Transport"
		),
		NULL,
	},

	{"protocol", transport_get_protocol, NULL,
		PyDoc_STR(
			"The protocol used by the Transport as a tuple: (name, major, minor)."
		),
		NULL,
	},

	{"standard", transport_get_standard, NULL,
		PyDoc_STR(
			"The protocol standard used by the Transport as a tuple: (org, std, id)."
		),
		NULL,
	},

	{"peer", transport_get_peer_certificate, NULL,
		PyDoc_STR(
			"Get the peer certificate. If the Transport has yet to receive it, "
			"&None will be returned."
		),
		NULL
	},

	{"receive_closed", transport_get_receive_closed, NULL,
		PyDoc_STR(
			"Whether shutdown state has been received from the peer."
		),
		NULL
	},

	{"transmit_closed", transport_get_transmit_closed, NULL,
		PyDoc_STR(
			"Whether the shutdown state has been sent to the peer."
		),
		NULL
	},

	{"violation", transport_get_violation, NULL,
		PyDoc_STR(
			"Tuple describing the violation; None if none."
		),
		NULL
	},

	{NULL,},
};

static PyObj
transport_repr(PyObj self)
{
	Transport tls = (Transport) self;
	char *tls_state;
	PyObj rob;

	tls_state = (char *) SSL_state_string(tls->tls_state);

	rob = PyUnicode_FromFormat("<%s [%s] at %p>", Py_TYPE(self)->tp_name, tls_state, self);
	return(rob);
}

static int
transport_clear(PyObj self)
{
	Transport tls = (Transport) self;

	Py_XDECREF(tls->output_queue);
	Py_XDECREF(tls->ctx_object);
	Py_XDECREF(tls->recv_closed_cb);
	Py_XDECREF(tls->send_queued_cb);

	(tls->output_queue) = NULL;
	(tls->ctx_object) = NULL;
	(tls->recv_closed_cb) = NULL;
	(tls->send_queued_cb) = NULL;

	return(0);
}

static int
transport_traverse(PyObj self, visitproc visit, void *arg)
{
	Transport tls = (Transport) self;

	Py_VISIT(tls->output_queue);
	Py_VISIT(tls->ctx_object);
	Py_VISIT(tls->recv_closed_cb);
	Py_VISIT(tls->send_queued_cb);

	return(0);
}

static void
transport_dealloc(PyObj self)
{
	Transport tls = (Transport) self;

	if (tls->tls_state == NULL)
		SSL_free(tls->tls_state);

	transport_clear(self);
	Py_TYPE(self)->tp_free(self);
}

static PyObj
transport_new_server(PyTypeObject *typ, Context ctx)
{
	Transport tls;

	tls = create_tls_state(typ, ctx);
	if (tls == NULL)
		return(NULL);

	SSL_set_accept_state(tls->tls_state);

	if (SSL_do_handshake(tls->tls_state) != 0 && library_error())
		goto error;

	return((PyObj) tls);

	error:
	{
		Py_DECREF((PyObj) tls);
		return(NULL);
	}
}

static PyObj
transport_new_client(PyTypeObject *typ, Context ctx, PyObj hostname)
{
	Transport tls;

	tls = create_tls_state(typ, ctx);
	if (tls == NULL)
		return(NULL);

	if (hostname != NULL)
	{
		if (_transport_set_hostname(tls, hostname))
			goto error;
	}

	SSL_set_connect_state(tls->tls_state);

	if (SSL_do_handshake(tls->tls_state) != 0 && library_error())
		goto error;

	return((PyObj) tls);

	error:
	{
		Py_DECREF((PyObj) tls);
		return(NULL);
	}
}

#ifndef ADAPTER_TRANSPORT_NEW
	#define ADAPTER_TRANSPORT_NEW create_tls_state
#endif

#if defined(ADAPTER_CLIENT)
static PyObj
transport_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {"context", "hostname", "certificate", NULL,};
	Context ctx = NULL;
	PyObj hostname = NULL;
	PyObj crt = NULL;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "O|OO", kwlist,
			&ctx,
			&hostname,
			&crt))
		return(NULL);

	return(ADAPTER_TRANSPORT_NEW(subtype, ctx, hostname));
}
#else
static PyObj
transport_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {"context", NULL,};
	Context ctx = NULL;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "O", kwlist, &ctx))
		return(NULL);

	return(ADAPTER_TRANSPORT_NEW(subtype, ctx));
}
#endif

PyDoc_STRVAR(transport_doc, "OpenSSL Secure Transfer State.");

static PyTypeObject
TransportType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	PYTHON_MODULE_PATH("Transport"), /* tp_name */
	sizeof(struct Transport),        /* tp_basicsize */
	0,                               /* tp_itemsize */
	transport_dealloc,               /* tp_dealloc */
	NULL,                            /* tp_print */
	NULL,                            /* tp_getattr */
	NULL,                            /* tp_setattr */
	NULL,                            /* tp_compare */
	transport_repr,                  /* tp_repr */
	NULL,                            /* tp_as_number */
	NULL,                            /* tp_as_sequence */
	NULL,                            /* tp_as_mapping */
	NULL,                            /* tp_hash */
	NULL,                            /* tp_call */
	NULL,                            /* tp_str */
	NULL,                            /* tp_getattro */
	NULL,                            /* tp_setattro */
	NULL,                            /* tp_as_buffer */
	Py_TPFLAGS_BASETYPE|
	Py_TPFLAGS_HAVE_GC|
	Py_TPFLAGS_DEFAULT,              /* tp_flags */
	transport_doc,                   /* tp_doc */
	transport_traverse,              /* tp_traverse */
	transport_clear,                 /* tp_clear */
	NULL,                            /* tp_richcompare */
	0,                               /* tp_weaklistoffset */
	NULL,                            /* tp_iter */
	NULL,                            /* tp_iternext */
	transport_methods,               /* tp_methods */
	transport_members,               /* tp_members */
	transport_getset,                /* tp_getset */
	NULL,                            /* tp_base */
	NULL,                            /* tp_dict */
	NULL,                            /* tp_descr_get */
	NULL,                            /* tp_descr_set */
	0,                               /* tp_dictoffset */
	NULL,                            /* tp_init */
	NULL,                            /* tp_alloc */
	transport_new,                   /* tp_new */
};

#define PYTHON_TYPES() \
	ID(Key) \
	ID(Certificate) \
	ID(Context) \
	ID(Transport)

#define MODULE_FUNCTIONS()

static void load_implementation(void) __attribute__((constructor));
static void
load_implementation(void)
{
	/*
		// Initialize OpenSSL.
	*/
	#if OPENSSL_VERSION_NUMBER < 0x10100000L
		SSL_library_init();
	#else
		OPENSSL_init_ssl(0, NULL);
	#endif

	SSL_load_error_strings();
	ERR_load_BIO_strings();
	ERR_load_crypto_strings();
	OpenSSL_add_ssl_algorithms();
	ERR_clear_error();
}

static int
init_implementation_data(PyObj module)
{
	if (PyExc_TransportSecurityError == NULL)
	{
		PyExc_TransportSecurityError = PyErr_NewException("openssl.IError", NULL, NULL);
		if (PyExc_TransportSecurityError == NULL)
			goto error;
	}
	else
		Py_INCREF(PyExc_TransportSecurityError);

	if (PyModule_AddObject(module, "IError", PyExc_TransportSecurityError))
		goto error;

	if (PyModule_AddIntConstant(module, "version_code", OPENSSL_VERSION_NUMBER))
		goto error;

	if (PyModule_AddStringConstant(module, "version", OPENSSL_VERSION_TEXT))
		goto error;

	if (PyModule_AddStringConstant(module, "ciphers", FAULT_OPENSSL_CIPHERS))
		goto error;

	/*
		// Break up the version into sys.version_info style tuple.
		// 0x1000105fL is 1.0.1e final
	*/
	{
		int patch_code = ((OPENSSL_VERSION_NUMBER >> 4) & 0xFF);
		int status_code = (OPENSSL_VERSION_NUMBER & 0xF);
		char *status = NULL, *patch = NULL, patch_char[2];

		switch (status_code)
		{
			case 0:
				status = "dev";
			break;

			case 0xF:
				status = "final";
			break;

			default:
				status = "beta";
			break;
		}

		switch (patch_code)
		{
			case 0:
				patch = NULL;
			break;
			default:
				patch_code += (int) 'a';
				patch_char[0] = patch_code - 1;
				patch_char[1] = '\0';
				patch = patch_char;
			break;
		}

		version_info = Py_BuildValue("(iiiss)",
			(OPENSSL_VERSION_NUMBER >> 28) & 0xFF,
			(OPENSSL_VERSION_NUMBER >> 20) & 0xFF,
			(OPENSSL_VERSION_NUMBER >> 12) & 0xFF,
			patch, status
		);

		if (PyModule_AddObject(module, "version_info", version_info))
			goto error;
	}

	/*
		// Initialize types
	*/
	#define ID(NAME) \
		if (PyType_Ready((PyTypeObject *) &( NAME##Type ))) \
			goto error; \
		if (PyModule_AddObject(module, #NAME, (PyObj) &( NAME##Type )) < 0) \
			goto error;
		PYTHON_TYPES()
	#undef ID

	return(0);
	error:
	{
		return(-1);
	}
}
