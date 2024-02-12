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

/**
	// Process the codepoints in the string handling cases
	// not covered by wcwidth.

	// Sequences are presumed valid; when encountered, the character
	// with the maximum cell count is used as the sequence cell count.

	// This needs to be changed to only use the maximum given that wcswidth
	// does recognize the sequence.
*/
static long
measure(wchar_t *wcv, size_t ws, unsigned char ctlen, unsigned char tablen)
{
	long prev = 0, w = 0, max = 0, seq = 0;
	size_t offset = 0;
	wchar_t (*wca)[ws] = (wchar_t (*)[]) wcv;

	while (offset < ws)
	{
		long lw = 0;
		wchar_t c = (*wca)[offset];

		switch (c)
		{
			/* Tabsize */
			case L'\t':
				lw = tablen;
			break;

			/* Zero widths. */
			case 0x2060:
			case 0x200B:
			case 0xFEFF:
			{
				/* ZWS and ZWNBS */
				lw = 0;
			}
			break;

			/* ZWNJ Break */
			case 0x200C:
			{
				if (seq > 0)
					seq = 1;
			}
			break;

			/* ZWJ Sequence if any */
			case 0x200D:
			{
				/* +0, continue sequence */
				seq = 3;

				/* Continue sequence */
				if (max == 0)
					max = prev;
			}
			break;

			/* Emoji Variant */
			case 0xFE0F:
			{
				/*
					// Calculate difference from the expected emoji size.
				*/
				lw = 2 - prev;
			}

			/* Text Variant */
			case 0xFE0E:
			{
				/*
					// Calculate the difference from expected text size.

					// Inaccurate if the former character is not an emoji.
				*/
				lw = 1 - prev;
			}
			break;

			/* Variant Selectors */
			case 0xFE00:
			case 0xFE01:
			case 0xFE02:
			case 0xFE03:
			case 0xFE04:
			case 0xFE05:
			case 0xFE06:
			case 0xFE07:
			case 0xFE08:
			case 0xFE09:
			case 0xFE0A:
			case 0xFE0B:
			case 0xFE0C:
			case 0xFE0D:
			{
				lw = 0;
			}
			break;

			default:
			{
				if (c < 32)
				{
					/* Low ASCII */
					lw = ctlen;
				}
				else if (c >= 0x1F1E6 && c <= 0x1F1FF)
				{
					/* flag range; only double width if consecutive */
					if (offset + 1 < ws)
					{
						wchar_t n = (*wca)[offset+1];

						if (n >= 0x1F1E6 && n <= 0x1F1FF)
						{
							++offset;
							lw = 2;
						}
						else
							lw = 1;
					}
					else
						lw = 1;
				}
				else
				{
					lw = wcwidth(c);
					if (lw < 0)
					{
						/*
							// Presume single.
						*/
						lw = 1;
					}
				}
			}
			break;
		}

		/* Sequence in progress? */
		if (seq > 0)
		{
			--seq;
			if (seq > 0)
			{
				/* Check maximum */
				if (lw > max)
				{
					w += (lw - max);
					max = lw;
				}
			}
			else
			{
				/* Terminate sequence */
				max = 0;
				w += lw;
			}
		}
		else
		{
			/* Non-sequence case, add identified cell count. */
			w += lw;
		}

		prev = lw; /* Needed for sequence termination. */
		++offset;
	}

	return(w);
}

/**
	// Cell count of string with some sequence and Variant Selector awareness.
*/
static PyObj
cells(PyObj self, PyObj args)
{
	#ifndef CELL_STACK_ALLOC
		#define CELL_STACK_ALLOC 16
	#endif

	int width, ctlen = 0, tablen = 4;
	Py_ssize_t len, size;
	PyObj str;

	if (!PyArg_ParseTuple(args, "U|ii", &str, &ctlen, &tablen))
		return(NULL);

	len = PyUnicode_GET_LENGTH(str);
	if (len < CELL_STACK_ALLOC)
	{
		/* Use stack for small strings. */
		wchar_t sawc[CELL_STACK_ALLOC];

		size = PyUnicode_AsWideChar(str, (wchar_t *) sawc, CELL_STACK_ALLOC);
		if (size == -1)
			return(NULL);

		width = measure(&sawc, size, ctlen, tablen);
	}
	else
	{
		wchar_t *wstr;

		wstr = PyUnicode_AsWideCharString(str, &size);
		if (wstr == NULL)
			return(NULL);

		width = measure(wstr, size, ctlen, tablen);
		PyMem_Free(wstr);
	}

	return(PyLong_FromLong((long) width));
}

#define MODULE_FUNCTIONS() \
	PYMETHOD(encoding, get_encoding, METH_NOARGS, NULL) \
	PYMETHOD(setlocale, dsetlocale, METH_NOARGS, NULL) \
	PYMETHOD(cells, cells, METH_VARARGS, NULL)

#include <fault/metrics.h>
#include <fault/python/module.h>
INIT(module, 0, PyDoc_STR("interfaces to system text services: wcswidth and setlocale."))
{
	return(0);
}
