/**
	// &.kernel module.
*/
#include <errno.h>
#include <spawn.h>
#include <pthread.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/utsname.h>
#include <sys/wait.h>

#include <fault/libc.h>
#include <fault/internal.h>
#include <fault/python/environ.h>

#include "Scheduling.h"
#include "invocation.h"

/*
	// For fork callbacks.
*/
static PyObj process_module = NULL;
static int exit_signal = -1;
static pid_t exit_for_pid = -1;

static PyObj
set_process_title(PyObj mod, PyObj title)
{
	PyObj bytes;

	#if defined(__MACH__) || defined(__linux__)
		;
	#else
		/*
			// No support on darwin.
		*/
		bytes = PyUnicode_AsUTF8String(title);

		if (bytes == NULL)
			return(NULL);

		setproctitle("%s", PyBytes_AS_STRING(bytes));
		Py_DECREF(bytes);
	#endif

	Py_RETURN_NONE;
}

static pthread_mutex_t forking_mutex = PTHREAD_MUTEX_INITIALIZER;
int forking_pipe[2] = {-1,-1};
struct inherit {
	pid_t process_id;
};

static void
prepare(void)
{
	pthread_mutex_lock(&forking_mutex);
	pipe(forking_pipe);
}

static struct inherit fork_data = {-1};

/**
	// Execute the &.process._after_fork_parent object from a pending call.
*/
static int
_after_fork_parent(void *pc_param)
{
	PyObj rob, ctx;

	rob = PyObject_CallMethod(process_module, "_after_fork_parent", "i", (int) pc_param);
	Py_XDECREF(rob);

	return(rob == NULL ? -1 : 0);
}

static void
parent(void)
{
	if (read(forking_pipe[0], &fork_data, sizeof(fork_data)) < sizeof(fork_data))
	{
		fork_data.process_id = -1;
		errno = 0;
	}

	close(forking_pipe[0]);
	close(forking_pipe[1]);
	forking_pipe[0] = -1;
	forking_pipe[1] = -1;
	pthread_mutex_unlock(&forking_mutex);

	retry:
	{
		uintptr_t param = fork_data.process_id;

		if (Py_AddPendingCall(_after_fork_parent, (void *) param))
		{
			goto retry;
		}
	}

	fork_data.process_id = -1;
}

/**
	// Execute the &.process._after_fork_child object from a pending call.
*/
static int
_after_fork_child(void *pc_param)
{
	PyObj rob;
	rob = PyObject_CallMethod(process_module, "_after_fork_child", "");
	Py_XDECREF(rob);
	return(rob == NULL ? -1 : 0);
}

/**
	// Synchronize with the parent process.
*/
static void
child(void)
{
	PyObj rob = Py_True;
	struct inherit buf = {-1};

	buf.process_id = getpid();

	write(forking_pipe[1], &buf, sizeof(buf));
	errno = 0;

	close(forking_pipe[0]);
	close(forking_pipe[1]);
	forking_pipe[0] = -1;
	forking_pipe[1] = -1;
	pthread_mutex_unlock(&forking_mutex);

	retry:
	{
		if (Py_AddPendingCall(_after_fork_child, NULL))
		{
			goto retry;
		}
	}
}

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

		/* XXX: O(NM) bloomfilter? ;) */
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
	// Ensure that the kport is preserved across process images.
	// Used by system to hold on to listening sockets.

	// Generally, most file descriptors created by &.system will have
	// the FD_CLOEXEC flag set.
*/
static PyObj
kport_clear_cloexec(PyObj mod, PyObj seq)
{
	long fd;

	PyLoop_ForEachLong(seq, &fd)
	{
		int flag = fcntl((int) fd, F_GETFD, 0);

		if (flag == -1)
		{
			PyErr_SetFromErrno(PyExc_OSError);
			break;
		}

		flag = fcntl((int) fd, F_SETFD, (flag & (~FD_CLOEXEC)));
		if (flag == -1)
		{
			PyErr_SetFromErrno(PyExc_OSError);
			break;
		}
	}
	PyLoop_CatchError(seq)
	{
		return(NULL);
	}
	PyLoop_End(seq)

	Py_RETURN_NONE;
}

static PyObj
kport_set_cloexec(PyObj mod, PyObj seq)
{
	long fd;

	PyLoop_ForEachLong(seq, &fd)
	{
		int flag = fcntl((int) fd, F_GETFD, 0);

		if (flag == -1)
		{
			PyErr_SetFromErrno(PyExc_OSError);
			break;
		}

		flag = fcntl((int) fd, F_SETFD, (flag | FD_CLOEXEC));
		if (flag == -1)
		{
			PyErr_SetFromErrno(PyExc_OSError);
			break;
		}
	}
	PyLoop_CatchError(seq)
	{
		return(NULL);
	}
	PyLoop_End(seq)

	Py_RETURN_NONE;
}

#define KPORT_TRANSFER(NAME, KPC) \
	int kp_##KPC(kport_t, kport_t *, uint32_t); \
	STATIC(PyObj) \
	k_##NAME(PyObj module, PyObj args, PyObj kw) \
	{ \
		Py_buffer kpv; \
		int aq = 0, limit = -1, offset = -1; \
		kport_t kp = -1; \
		static char *kwlist[] = {"kport", "ports", "limit", "offset", NULL}; \
		\
		if (!PyArg_ParseTupleAndKeywords(args, kw, "iw*|$ii", kwlist, &kp, &kpv, &limit, &offset)) \
			return(NULL); \
		\
		if (offset < 0) \
			offset = 0; \
		\
		if (limit < 0) \
			limit = ((kpv.len - (offset * sizeof(kport_t))) / sizeof(kport_t)); \
		\
		_PY_THREAD_SUSPEND_ \
		{ \
			aq = kp_##KPC(kp, kpv.buf + (offset * sizeof(kport_t)), limit); \
		} \
		_PY_THREAD_RESUME_ \
		PyBuffer_Release(&kpv); \
		if (aq < 0) \
		{ \
			PyErr_SetFromErrno(PyExc_OSError); \
			errno = 0; \
			return(NULL); \
		} \
		\
		Py_RETURN_INTEGER(aq); \
	}

KPORT_TRANSFER(accept_ports, accept);
KPORT_TRANSFER(transmit_ports, transmit);
KPORT_TRANSFER(receive_ports, receive);
KPORT_TRANSFER(alloc_meta, alloc_meta);
KPORT_TRANSFER(alloc_pipe, alloc_unidirectional);
KPORT_TRANSFER(alloc_socketpair, alloc_bidirectional);

/*
	// Retrieve a reference to the process_module module and register
	// the atfork handlers.

	// Only runs once and there is currently no way to update the
	// process_module entry meaning that system.process should not be reloaded.
*/
static PyObj
k_initialize(PyObj mod, PyObj ctx)
{
	if (process_module != NULL)
	{
		/* Already configured */
		Py_RETURN_NONE;
	}

	process_module = ctx;
	Py_INCREF(process_module);

	if (pthread_atfork(prepare, parent, child))
	{
		PyErr_SetFromErrno(PyExc_OSError);
		return(NULL);
	}

	Py_RETURN_NONE;
}

/**
	// waitid interface handling retry logic and reporting Python errors.

	// Usage is primarily intended for waiting or reaping, but also neither
	// in the case of &k_test_process where it just reports on the child's
	// running status.
*/
static pid_t
wait_or_reap(int *status, pid_t pid, int options)
{
	int err;
	pid_t rpid = 0;
	short retry_count = 0;

	retry:
	{
		siginfo_t si = {0,};

		if (pid < -1)
			err = waitid(P_PGID, -pid, &si, WEXITED | options);
		else if (pid == -1)
			err = waitid(P_ALL, pid, &si, WEXITED | options);
		else
			err = waitid(P_PID, pid, &si, WEXITED | options);

		if (options & WNOWAIT)
			rpid = si.si_pid;
		else
			rpid = pid;

		switch (si.si_code)
		{
			case CLD_EXITED:
				*status = si.si_status;
			break;

			case CLD_DUMPED:
			case CLD_KILLED:
				*status = -si.si_status;
			break;

			case 0:
			default:
				if (options & WNOHANG)
				{
					rpid = 0;
					*status = si.si_pid;
				}
			break;
		}
	}

	if (err)
	{
		switch (errno)
		{
			case EINTR:
			{
				if (PyErr_Occurred() || PyErr_CheckSignals())
					return(-1);
			}
			break;

			case ECHILD:
			{
				if (options & WNOHANG && options & WNOWAIT)
				{
					// Special case for k_test_process.
					return(-2);
				}
			}
			default:
				PyErr_SetFromErrno(PyExc_OSError);
				return(-1);
			break;
		}

		// EINTR without Python exception being set.
		assert(errno == EINTR);

		if (options & WNOHANG)
		{
			// Attempt to control an unusual exception case where EINTR
			// is somehow reported despiite the process being expected
			// to have exited. (WNOHANG)
			++retry_count;
			if (retry_count >= 4)
			{
				PyErr_SetString(PyExc_RuntimeError, "reap exceeded retry limit");
				return(-1);
			}

			goto retry;
		}
		else
			goto retry; // Unlimited under k_wait_process.
	}

	return(rpid);
}

/**
	// Test whether the process exists or not.
*/
static PyObj
k_test_process(PyObj module, PyObj args)
{
	int status = 0;
	pid_t rpid, pid = -1;

	if (!PyArg_ParseTuple(args, (char[]){'|', Py_FORMAT_CODE(pid)[0], '\0'}, &pid))
		return(NULL);

	rpid = wait_or_reap(&status, pid, WNOWAIT|WNOHANG);
	switch (rpid)
	{
		case -1:
			return(NULL);
		break;

		case -2:
			// ECHILD
			rpid = 0;
		break;

		case 0:
			rpid = pid;
		break;
	}

	return(Py_NEW_VALUE(rpid));
}

/**
	// Wait for process exit, but don't reap.
*/
static PyObj
k_wait_process(PyObj module, PyObj args)
{
	int status = 0;
	pid_t rpid, pid = -1;

	if (!PyArg_ParseTuple(args, (char[]){'|', Py_FORMAT_CODE(pid)[0], '\0'}, &pid))
		return(NULL);

	rpid = wait_or_reap(&status, pid, WNOWAIT);
	if (rpid == -1)
		return(NULL);

	return(Py_NEW_VALUE(rpid));
}

/**
	// Reap process, but don't wait for exit.
*/
static PyObj
k_reap_process(PyObj module, PyObj pid_ob)
{
	int exitcode = 0;
	pid_t pid = PyLong_AsPid(pid_ob);

	if (pid < 1)
	{
		if (!PyErr_Occurred())
			PyErr_SetString(PyExc_ValueError, "reap requires a process identifier greater than zero");

		return(NULL);
	}

	switch (wait_or_reap(&exitcode, pid, WNOHANG))
	{
		case -1:
			return(NULL);
		break;

		case 0:
			errno = EBUSY;
			PyErr_SetFromErrno(PyExc_OSError);
			return(NULL);
		break;

		default:
			;
		break;
	}

	return(Py_NEW_VALUE(exitcode));
}

extern PyTypeObject EventType;
extern PyTypeObject LinkType;
extern PyTypeObject SchedulerType;
extern PyTypeObject InvocationType;

extern PyTypeObject KPortsType;
KPorts kports_alloc(kport_t, Py_ssize_t);
KPorts kports_create(kport_t[], Py_ssize_t);
struct KPortsAPI _kp_apis = {
	&KPortsType,
	kports_alloc,
	kports_create,
};

#include <kext.h>
CONCEAL(struct ExtensionInterfaces)
fault_python_ext_if = {
	&_kp_apis,
	NULL,
};

#define PortsType KPortsType
#define PYTHON_TYPES() \
	ID(Ports) \
	ID(Event) \
	ID(Link) \
	ID(Invocation) \
	ID(Scheduler)

#define k_preserve kport_clear_cloexec
#define k_released kport_set_cloexec
#define k_set_process_title set_process_title

#define PyMethod_Id(N) k_##N
#define MODULE_FUNCTIONS() \
	PyMethod_Variable(test_process), \
	PyMethod_Variable(wait_process), \
	PyMethod_Sole(reap_process), \
	\
	PyMethod_Sole(set_process_title), \
	\
	PyMethod_Sole(preserve), \
	PyMethod_Sole(released), \
	\
	PyMethod_Keywords(accept_ports), \
	PyMethod_Keywords(receive_ports), \
	PyMethod_Keywords(transmit_ports), \
	PyMethod_Keywords(alloc_meta), \
	PyMethod_Keywords(alloc_pipe), \
	PyMethod_Keywords(alloc_socketpair), \
	\
	PyMethod_Sole(initialize),

#include <fault/metrics.h>
#include <fault/python/module.h>
INIT(module, 0)
{
	PyObj xi_ob = NULL, kp_api_ob = NULL;

	#define ID(NAME) \
		if (PyType_Ready((PyTypeObject *) &( NAME##Type ))) \
			goto error; \
		Py_INCREF((PyObj) &( NAME##Type )); \
		if (PyModule_AddObject(module, #NAME, (PyObj) &( NAME##Type )) < 0) \
			{ Py_DECREF((PyObj) &( NAME##Type )); goto error; }
		PYTHON_TYPES()
	#undef ID

	xi_ob = PyCapsule_New(&fault_python_ext_if, "__xi__", NULL);
	if (xi_ob == NULL)
		goto error;

	if (PyModule_AddObject(module, "__xi__", xi_ob))
		goto error;

	kp_api_ob = PyCapsule_New(&_kp_apis, "_kports_api", NULL);
	if (kp_api_ob == NULL)
		goto error;

	if (PyModule_AddObject(module, "_kports_api", kp_api_ob))
		goto error;

	return(0);

	error:
	{
		Py_XDECREF(xi_ob);
		Py_XDECREF(kp_api_ob);
		return(-1);
	}
}
#undef PyMethod_Id
