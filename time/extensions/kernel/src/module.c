/**
	# Interface to the kernel's clock using mostly POSIX interfaces.

	# gettimeofday/settimeofday, adjtime, and monotonic timer access.

	# These C functions perform conversion into Y2K+1 offsets for efficiency.
**/
#include <sys/types.h>
#include <sys/time.h>

#define MIN(x,y) (x < y ? x : y)

#define NS_IN_SEC 1000000000
#define US_IN_SEC 1000000

#ifdef __MACH__
#include <mach/clock.h>
#include <mach/mach.h>
#include <pthread.h>
#warning MACH_CLOCK_ID
#define LOCAL_MONOTONIC_CLOCK_ID SYSTEM_CLOCK
#define MACH(...) __VA_ARGS__
#else
#define MACH(...)
#endif

#ifdef __FreeBSD__
/*
	# Uptime clock for portability across processes.
*/
#warning FREEBSD_CLOCK_ID
#define LOCAL_MONOTONIC_CLOCK_ID CLOCK_UPTIME_FAST
#endif

#ifndef LOCAL_MONOTONIC_CLOCK_ID
#warning POSIX_CLOCK_ID
/*
	# linux etc?
*/
#define LOCAL_MONOTONIC_CLOCK_ID CLOCK_MONOTONIC
#endif

/*
	# If Python didn't find it, it won't include it.
	# However, it's quite necessary.
*/
#ifndef HAVE_STDINT_H
#include <stdint.h>
#endif

#ifndef EPOCH_YEAR
#define EPOCH_YEAR 2000
#endif

#include <fault/libc.h>
#include <fault/python/environ.h>

MACH(static clock_serv_t applestuff);

typedef struct Chronometer *Chronometer;

#define seconds_in_day (60 * 60 * 24)
/**
	# Use a Y2K+1 epoch. (+1 for weekstart alignment)
	# It's nearly aligned on a gregorian cycle and a week cycle.
**/
const time_t unix_epoch_delta = (((((EPOCH_YEAR-1970) * 365) + 7) * seconds_in_day) + seconds_in_day);

/**
	# Wallclock snapshot as an int with microsecond precision.
**/
static PyObj
snapshot_us(PyObj self)
{
	struct timeval tv = {0,0};
	unsigned long long ull;

	if (gettimeofday(&tv, NULL))
	{
		PyErr_SetFromErrno(PyExc_OSError);
		return(NULL);
	}

	/* adjust relative to 2000-01-02 (first sunday) */
	ull = tv.tv_sec;
	ull -= unix_epoch_delta;
	ull *= 1000000;
	ull += tv.tv_usec;

	return(PyLong_FromLongLong(ull));
}

/**
	# Wallclock snapshot as an int with nanosecond precision.
**/
static PyObj
snapshot_ns(PyObj self)
{
	unsigned long long ull;
	struct timespec ts;

	#ifdef __MACH__
		/*
			# @2012
			# The mach interfaces to CALENDAR_CLOCK (clock_get_time)
			# are in usec precision. Just use gettimeofday. :(
		*/
		struct timeval tv;
		if (gettimeofday(&tv, NULL))
		{
			PyErr_SetFromErrno(PyExc_OSError);
			return(NULL);
		}
		ts.tv_sec = tv.tv_sec;
		ts.tv_nsec = tv.tv_usec * 1000;
	#else
		if (clock_gettime(CLOCK_REALTIME, &ts))
		{
			PyErr_SetFromErrno(PyExc_OSError);
			return(NULL);
		}
	#endif

	ull = ts.tv_sec;
	/* adjust relative to 2000-01-02 (first sunday) */
	ull -= unix_epoch_delta;
	ull *= 1000000000; /* number of nanoseconds in second */
	ull += ts.tv_nsec;

	return(PyLong_FromUnsignedLongLong(ull));
}

static PyObj
sleep_us(PyObj self, PyObj usec)
{
	int r;
	unsigned long long ull;
	struct timespec request, actual;

	ull = PyLong_AsUnsignedLongLong(usec);
	if (PyErr_Occurred())
		return(NULL);

	Py_BEGIN_ALLOW_THREADS

	ull = ull * 1000;
	request.tv_sec = ull / 1000000000;
	request.tv_nsec = ull % 1000000000;

	r = nanosleep(&request, &actual);

	Py_END_ALLOW_THREADS

	if (r == 0)
	{
		Py_INCREF(usec);
		return(usec);
	}

	ull = actual.tv_sec * 1000000000;
	ull = ull + actual.tv_nsec;

	return(PyLong_FromUnsignedLongLong(ull));
}

static PyObj
sleep_ns(PyObj self, PyObj nsec)
{
	int r;
	unsigned long long ull;
	struct timespec request, actual;

	ull = PyLong_AsUnsignedLongLong(nsec);
	if (PyErr_Occurred())
		return(NULL);

	request.tv_sec = ull / 1000000000;
	request.tv_nsec = ull % 1000000000;

	Py_BEGIN_ALLOW_THREADS

	r = nanosleep(&request, &actual);

	Py_END_ALLOW_THREADS

	if (r == 0)
	{
		Py_INCREF(nsec);
		return(nsec);
	}

	ull = actual.tv_sec * 1000000000;
	ull = ull + actual.tv_nsec;

	return(PyLong_FromUnsignedLongLong(ull));
}

/**
	# Chronometer object for tracking elapsed time.
**/
struct Chronometer {
	PyObject_HEAD

	unsigned long long previous;
	unsigned long long count;
};

static unsigned long long
chronometer_fetch(Chronometer cm)
{
	unsigned long long r;

	#ifdef __MACH__
		mach_timespec_t ts;
		clock_get_time(applestuff, &ts);
	#else
		struct timespec ts;
		clock_gettime(LOCAL_MONOTONIC_CLOCK_ID, &ts);
	#endif

	r = ts.tv_sec;
	r *= 1000000000;
	r += ts.tv_nsec;
	return(r);
}

static PyObj
chronometer_iter(PyObj self)
{
	Py_INCREF(self);
	return(self);
}

static PyObj
chronometer_snapshot(PyObj self)
{
	Chronometer cm = (Chronometer) self;
	return(PyLong_FromUnsignedLongLong(chronometer_fetch(cm) - cm->previous));
}

static PyObj
chronometer_next(PyObj self)
{
	Chronometer cm = (Chronometer) self;
	unsigned long long l;
	unsigned long long nsec;

	l = chronometer_fetch(cm);
	if (cm->count == 0)
		nsec = 0;
	else
		nsec = l - cm->previous;
	cm->previous = l;
	++cm->count;

	return(PyLong_FromUnsignedLongLong(nsec));
}

static PyObj
chronometer_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	Chronometer cm;
	PyObj rob;

	rob = PyAllocate(subtype);
	if (rob == NULL)
		return(NULL);

	cm = (Chronometer) rob;
	cm->count = 0;

	cm->previous = chronometer_fetch(cm);

	return(rob);
}

static PyMemberDef
chronometer_members[] = {
	{"count", T_ULONGLONG, offsetof(struct Chronometer, count), 0,
		PyDoc_STR("total number of queries issued to the meter")},
	{NULL,},
};

static PyMethodDef
chronometer_methods[] = {
	{"snapshot", (PyCFunction) chronometer_snapshot, METH_NOARGS,
		PyDoc_STR("get a snapshot of meter in nanoseconds")},
	{NULL},
};

const char chronometer_doc[] =
"Chronometers are objects track the amount of elapsed time in the requested precision.\n"
;

static PyTypeObject
ChronometerType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	MODULE_QPATH("Chronometer"),	/* tp_name */
	sizeof(struct Chronometer),	/* tp_basicsize */
	0,										/* tp_itemsize */
	NULL,									/* tp_dealloc */
	NULL,									/* tp_print */
	NULL,									/* tp_getattr */
	NULL,									/* tp_setattr */
	NULL,									/* tp_compare */
	NULL,									/* tp_repr */
	NULL,									/* tp_as_number */
	NULL,									/* tp_as_sequence */
	NULL,									/* tp_as_mapping */
	NULL,									/* tp_hash */
	NULL,									/* tp_call */
	NULL,									/* tp_str */
	NULL,									/* tp_getattro */
	NULL,									/* tp_setattro */
	NULL,									/* tp_as_buffer */
	Py_TPFLAGS_BASETYPE|
	Py_TPFLAGS_DEFAULT,				/* tp_flags */
	chronometer_doc,					/* tp_doc */
	NULL,									/* tp_traverse */
	NULL,									/* tp_clear */
	NULL,									/* tp_richcompare */
	0,										/* tp_weaklistoffset */
	chronometer_iter,					/* tp_iter */
	chronometer_next,					/* tp_iternext */
	chronometer_methods,				/* tp_methods */
	chronometer_members,				/* tp_members */
	NULL,									/* tp_getset */
	NULL,									/* tp_base */
	NULL,									/* tp_dict */
	NULL,									/* tp_descr_get */
	NULL,									/* tp_descr_set */
	0,										/* tp_dictoffset */
	NULL,									/* tp_init */
	NULL,									/* tp_alloc */
	chronometer_new,					/* tp_new */
};

/*
 * Sleeper type for elapsing time.
 */
struct Sleeper {
	PyObject_HEAD

	unsigned long long remainder;
	unsigned int frequency, trips;
};

PyObj
sleeper_iter(PyObj self)
{
	Py_INCREF(self);
	return(self);
}

static PyObj
sleeper_next(PyObj self)
{
	struct Sleeper *s = (struct Sleeper *) self;
	struct timespec request, actual = {0,};

	char tripped = 0;

	unsigned long long current_frequency, current_remainder = 0, max_sleep;
	unsigned long long elapsed = 0, total = 0; /* nanoseconds */

	if (s->trips > 0)
	{
		--s->trips;
	}
	else while (s->remainder > 0)
	{
		int r = 0;
		current_frequency = s->frequency;
		current_remainder = s->remainder;

		Py_BEGIN_ALLOW_THREADS /* "outside" of Python */

		total += elapsed;
		elapsed = 0;
		request.tv_sec = 0;
		max_sleep = NS_IN_SEC / current_frequency;

		while (elapsed < current_remainder)
		{
			if (s->trips > 0)
			{
				tripped = 1;
				break;
			}

			/*
			 * The minimum is used to allow precision interrupts when the remainder changes.
			 */
			request.tv_nsec = MIN(max_sleep, current_remainder - elapsed);
			r = nanosleep(&request, &actual);

			if (r != 0)
			{
				elapsed += actual.tv_nsec;
				elapsed += (actual.tv_sec * NS_IN_SEC);
			}
			else
				elapsed += request.tv_nsec;

			if (r != 0 || s->frequency != current_frequency || s->remainder != current_remainder)
			{
				/*
				 * Break out of the sleep loop on any change or error.
				 */
				break;
			}
		}

		Py_END_ALLOW_THREADS

		if (tripped)
		{
			/*
			 * The sleeper was explicitly disturbed.
			 */
			s->trips -= 1;
			break;
		}

		/*
		 * Grab the GIL; check for configuration changes and respond accordingly.
		 */

		if (current_remainder == s->remainder)
		{
			current_remainder = s->remainder - elapsed;

			if (current_remainder > s->remainder)
			{
				/*
				 * Zero out on wrap.
				 */
				s->remainder = 0;
			}
			else
			{
				s->remainder = current_remainder;
			}
		}

		if (r != 0)
		{
			/*
			 * If the sleep function resulted in error,
			 * a value is yielded.
			 */
			break;
		}
	}

	return(PyLong_FromUnsignedLongLong(total + elapsed));
}

static PyObj
sleeper_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	struct Sleeper *s;
	PyObj rob;

	rob = PyAllocate(subtype);
	if (rob == NULL)
		return(NULL);

	s = (struct Sleeper *) rob;
	s->frequency = 100;
	s->remainder = 0;

	return(rob);
}

static PyMemberDef
sleeper_members[] = {
	{"frequency", T_ULONGLONG, offsetof(struct Sleeper, frequency), 0,
		PyDoc_STR("number of times per second that the remainder should be checked for updates")},
	{"remainder", T_ULONGLONG, offsetof(struct Sleeper, remainder), 0,
		PyDoc_STR("remaining units of time before the sleeper awakes")},
	{NULL,},
};

static PyObj
s_disturb(PyObj self)
{
	struct Sleeper *s = (struct Sleeper *) self;
	unsigned int next_trips = s->trips + 1;

	/*
	 * Increment the trips while holding the GIL.
	 * Trips are only decremented when the GIL is held.
	 *
	 * XXX: This should really be a conditional call to pthread_kill.
	 */
	if (next_trips > 0)
		s->trips = next_trips;

	Py_INCREF(Py_None);
	return(Py_None);
}

static PyMethodDef
sleeper_methods[] = {
	{"disturb", (PyCFunction) s_disturb, METH_NOARGS,
		PyDoc_STR("disturb the sleeper causing it to fall out of slumber")},
	{NULL},
};

const char sleeper_doc[] =
"Sleepers are objects that elapse time using a sleep function.\n"
"They sleep while the GIL is released but poll for timing changes at a configured frequency.\n"
"Sleepers provide a relatively efficient alarm device for timing purposes."
;

PyTypeObject
SleeperType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	MODULE_QPATH("Sleeper"),		/* tp_name */
	sizeof(struct Sleeper),			/* tp_basicsize */
	0,										/* tp_itemsize */
	NULL,									/* tp_dealloc */
	NULL,									/* tp_print */
	NULL,									/* tp_getattr */
	NULL,									/* tp_setattr */
	NULL,									/* tp_compare */
	NULL,									/* tp_repr */
	NULL,									/* tp_as_number */
	NULL,									/* tp_as_sequence */
	NULL,									/* tp_as_mapping */
	NULL,									/* tp_hash */
	NULL,									/* tp_call */
	NULL,									/* tp_str */
	NULL,									/* tp_getattro */
	NULL,									/* tp_setattro */
	NULL,									/* tp_as_buffer */
	Py_TPFLAGS_BASETYPE|
	Py_TPFLAGS_DEFAULT,				/* tp_flags */
	sleeper_doc,							/* tp_doc */
	NULL,									/* tp_traverse */
	NULL,									/* tp_clear */
	NULL,									/* tp_richcompare */
	0,										/* tp_weaklistoffset */
	sleeper_iter,						/* tp_iter */
	sleeper_next,						/* tp_iternext */
	sleeper_methods,					/* tp_methods */
	sleeper_members,					/* tp_members */
	NULL,									/* tp_getset */
	NULL,									/* tp_base */
	NULL,									/* tp_dict */
	NULL,									/* tp_descr_get */
	NULL,									/* tp_descr_set */
	0,										/* tp_dictoffset */
	NULL,									/* tp_init */
	NULL,									/* tp_alloc */
	sleeper_new,						/* tp_new */
};

#ifdef __MACH__
static void
INIT_MACH_PORT(void)
{
	host_get_clock_service(mach_host_self(), LOCAL_MONOTONIC_CLOCK_ID, &(applestuff));
}
#endif

/* METH_O, METH_VARARGS, METH_VARKEYWORDS, METH_NOARGS */
#define MODULE_FUNCTIONS() \
	PYMETHOD(snapshot_us, snapshot_us, METH_NOARGS, "get the time in microseconds") \
	PYMETHOD(snapshot_ns, snapshot_ns, METH_NOARGS, "get the time in microseconds") \
	PYMETHOD(sleep_us, sleep_us, METH_O, "sleep for the given number of microseconds") \
	PYMETHOD(sleep_ns, sleep_ns, METH_O, "sleep for the given number of nanoseconds")

#include <fault/python/module.h>

INIT("clock mechanics using common userland interfaces")
{
	PyObj mod = NULL;

	MACH(INIT_MACH_PORT());
	/* fork cases need to reinit the port */
	MACH(pthread_atfork(NULL, NULL, INIT_MACH_PORT));

	CREATE_MODULE(&mod);
	if (mod == NULL)
		return(NULL);

	if (PyType_Ready(&ChronometerType) != 0)
		goto fail;
	PyModule_AddObject(mod, "Chronometer", (PyObj) (&ChronometerType));

	if (PyType_Ready(&SleeperType) != 0)
		goto fail;
	PyModule_AddObject(mod, "Sleeper", (PyObj) (&SleeperType));

	return(mod);

fail:
	DROP_MODULE(mod);
	return(NULL);
}
/*
 * vim: ts=3:sw=3:noet:
 */
