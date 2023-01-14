/**
	// System text services.
*/
#include <wchar.h>
#include <locale.h>
#include <langinfo.h>

#include <fault/libc.h>
#include <fault/internal.h>
#include <fault/python/environ.h>

static PyObj
dsetlocale(PyObj self)
{
	char *selection = setlocale(LC_ALL, "");

	if (selection == NULL)
	{
		PyErr_Format(PyExc_RuntimeError,
			"could not set native environment locale; setlocale(2) returned NULL");
		return(NULL);
	}

	return(PyUnicode_FromString(selection));
}

static PyObj
get_encoding(PyObj self)
{
	char *encoding = nl_langinfo(CODESET);
	if (encoding[0] == '\000')
		Py_RETURN_NONE;

	return(PyUnicode_FromString(encoding));
}

#define MODULE_FUNCTIONS() \
	PYMETHOD(encoding, get_encoding, METH_NOARGS, \
		"get the CODESET string using the system's nl_langinfo(2)") \
	PYMETHOD(setlocale, dsetlocale, METH_NOARGS, \
		"limited setlocale(2) interface providing access to setting the native environment locale.")

#include <fault/metrics.h>
#include <fault/python/module.h>
INIT(module, 0, PyDoc_STR("interfaces to system text services: wcswidth and setlocale."))
{
	return(0);
}
