/**
	// Runtime control support.
*/
#include <errno.h>
#include <pthread.h>
#include <signal.h>

#include <fault/libc.h>
#include <fault/internal.h>
#include <fault/python/environ.h>
#include <frameobject.h>

static int
ltracefunc(PyObj ob, PyFrameObject *f, int event, PyObj arg)
{
	/*
		// TODO: debugger control tracefunc
	*/
	return(0);
}

/**
	// Set the trace object on a set of threads.
	// Only supports callable-object level.
	// This is intended for debuggers.
*/
static PyObj
trace(PyObj self, PyObj args)
{
	PyObj trace_func, thread_ids;
	Py_ssize_t i;
	long *tids;
	PyThreadState *start = PyThreadState_Get();
	PyThreadState *ts;
	Py_ssize_t nthreads;
	Py_tracefunc f = ltracefunc;

	if (!PyArg_ParseTuple(args, "OO", &trace_func, &thread_ids))
		return(NULL);

	nthreads = PySequence_Length(thread_ids);
	tids = PyMem_Malloc(nthreads * sizeof(long));
	if (tids == NULL)
		return(NULL);

	/*
		// Convert sequence to array of longs.
	*/
	for (i = 0; i < nthreads; ++i)
	{
		PyObj n = PySequence_GetItem(thread_ids, i);

		if (n != NULL)
		{
			tids[i] = PyLong_AsLong(n);
			Py_DECREF(n);
		}

		if (PyErr_Occurred())
		{
			/*
			 * Couldn't get item or failued to convert.
			 * Exit.
			 */
			PyMem_Free(tids);
			return(NULL);
		}
	}

	/*
		// Install the tracefunc on the matching threadstates.
	*/
	ts = start;
	do
	{
		ts = ts->next;

		/* XXX: O(NM) */
		for (i = 0; i < nthreads; ++i)
		{
			if (tids[i] == ts->thread_id)
			{
				ts->c_tracefunc = ltracefunc;
				ts->c_traceobj = trace_func;
				ts->c_profilefunc = NULL;
				Py_XDECREF(ts->c_profileobj);
				ts->c_profileobj = NULL;

				#if (PY_MAJOR_VERSION == 3) && (PY_MINOR_VERSION >= 10)
					#if (PY_MINOR_VERSION < 12)
						ts->cframe->use_tracing = 1;
					#endif
				#else
					ts->use_tracing = 1;
				#endif
			}
		}
	}
	while(ts != start);

	PyMem_Free(tids);

	Py_RETURN_NONE;
}

/**
	// AddPendingCall callback
*/
static int
_call(void *ob)
{
	PyObject *callable = ob;
	PyObject *ret = NULL;

	ret = PyObject_CallObject(ob, NULL);
	Py_XDECREF(ret);
	Py_DECREF(callable);

	return(ret == NULL ? -1 : 0);
}

/**
	// Expose AddPendingCall C-API to the Python language.
*/
static PyObj
interject(PyObj self, PyObj callable)
{
	PyObj rob = Py_True;

	Py_INCREF(callable);
	if (Py_AddPendingCall(_call, callable))
	{
		Py_DECREF(callable);
		rob = Py_False;
	}

	Py_INCREF(rob);
	return(rob);
}

static PyObj
interrupt(PyObj self, PyObj args)
{
	long tid;
	PyObj exc;

	if (!PyArg_ParseTuple(args, "lO", &tid, &exc))
		return(NULL);

	if (!PyThreadState_SetAsyncExc(tid, exc))
		return(NULL);

	Py_INCREF(Py_None);
	return(Py_None);
}

/**
	// Executed in atexit in order to preserve the signal's exit code.
*/
static pid_t _exit_signal_pid = -1;
static int _exit_signal = -1;
static void
__attribute__((destructor(150)))
_exit_by_signal(void)
{
	// Ignore this if it somehow forked after the exit_by_signal was called.
	if (_exit_signal_pid != -1 && _exit_signal_pid == getpid())
	{
		signal(_exit_signal, SIG_DFL);
		kill(_exit_signal_pid, _exit_signal);

		fprintf(stderr, "signalexit: signal, %d, did not terminate process\n", _exit_signal);
		abort();
	}
}

/**
	// Set _exit_by_signal trigger.
*/
static PyObj
signalexit(PyObj module, PyObj ob)
{
	long signo;
	pid_t p;

	signo = PyLong_AsLong(ob);
	if (PyErr_Occurred())
		return(NULL);

	_exit_signal_pid = getpid();
	_exit_signal = signo;

	Py_RETURN_NONE;
}

#define PYTHON_TYPES()
#define PyMethod_Id(N) N
#define MODULE_FUNCTIONS() \
	PyMethod_Variable(interrupt), \
	PyMethod_Sole(interject), \
	PyMethod_Variable(trace), \
	PyMethod_Sole(signalexit), \

#include <fault/metrics.h>
#include <fault/python/module.h>
INIT(module, 0)
{
	#define ID(NAME) \
		if (PyType_Ready((PyTypeObject *) &( NAME##Type ))) \
			goto error; \
		Py_INCREF((PyObj) &( NAME##Type )); \
		if (PyModule_AddObject(module, #NAME, (PyObj) &( NAME##Type )) < 0) \
			{ Py_DECREF((PyObj) &( NAME##Type )); goto error; }
		PYTHON_TYPES()
	#undef ID

	return(0);

	error:
	{
		return(-1);
	}
}
