/**
	// Implementation for POSIX clocks.

	// Creates a clock concept defined by &ClockworkType that provides
	// interfaces to retrieving a snapshot of the clock's state.
	// The two subclasses (&RealClockType and &MonotonicClockType) hardcode
	// the clockid_t to instances.
*/
#include <fault/libc.h>
#include <fault/python/environ.h>

#include "clockwork.h"

#if SYSTEM_FEATURES_clock_gettime_nsec_np
	static unsigned long long
	clockwork_get_positive_adjustment(Clockwork cw)
	{
		return clock_gettime_nsec_np(cw->cw_clockid) + (cw->cw_offset * NS_IN_SEC);
	}
#else
	static unsigned long long
	clockwork_get_positive_adjustment(Clockwork cw)
	{
		unsigned long long r;

		struct timespec ts;
		clock_gettime(cw->cw_clockid, &ts);

		r = ts.tv_sec + cw->cw_offset;
		r *= NS_IN_SEC;
		r += ts.tv_nsec;

		return(r);
	}
#endif

static PyObj
clockwork_set(PyObj self, PyObj args)
{
	Clockwork cw = (Clockwork) self;
	long long secs;
	struct timespec ts;

	if (!PyArg_ParseTuple(args, "L", &secs))
		return(NULL);

	clock_gettime(cw->cw_clockid, &ts);

	cw->cw_offset = (secs/NS_IN_SEC) - ts.tv_sec;

	Py_INCREF(self);
	return(self);
}

static PyObj
clockwork_get(PyObj self)
{
	unsigned long long r;

	r = clockwork_get_positive_adjustment((Clockwork) self);
	return(PyLong_FromUnsignedLongLong(r));
}

static PyObj
clockwork_snapshot(PyObj self)
{
	Clockwork cw = (Clockwork) self;
	struct timespec ts;

	clock_gettime(cw->cw_clockid, &ts);
	ts.tv_sec += cw->cw_offset;

	return(Py_BuildValue("Kl", ts.tv_sec, ts.tv_nsec));
}

static PyObj
clockwork_adjust(PyObj self, PyObj args)
{
	Clockwork cw = (Clockwork) self;
	long long secs;

	if (!PyArg_ParseTuple(args, "L", &secs))
		return(NULL);

	cw->cw_offset += secs;
	Py_INCREF(self);
	return(self);
}

static PyObj
clockwork_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {"posix_clock_id", NULL};
	long cid;
	Clockwork cw;
	PyObj rob;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "l", kwlist, &cid))
		return(NULL);

	rob = PyAllocate(subtype);
	if (rob == NULL)
		return(NULL);

	cw = (Clockwork) rob;
	cw->cw_clockid = (clockid_t) cid;
	cw->cw_offset = 0;

	return(rob);
}

static PyMemberDef
clockwork_members[] = {
	{"offset", T_LONGLONG, offsetof(struct Clockwork, cw_offset), 0, NULL},
	{NULL,},
};

static PyMethodDef
clockwork_methods[] = {
	{"snapshot", (PyCFunction) clockwork_snapshot, METH_NOARGS, NULL},
	{"get", (PyCFunction) clockwork_get, METH_NOARGS, NULL},
	{"set", (PyCFunction) clockwork_set, METH_VARARGS, NULL},
	{"adjust", (PyCFunction) clockwork_adjust, METH_VARARGS, NULL},
	{NULL},
};

static PyTypeObject
ClockworkType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	PYTHON_MODULE_PATH("Clockwork"),/* tp_name */
	sizeof(struct Clockwork),       /* tp_basicsize */
	0,                              /* tp_itemsize */
	NULL,                           /* tp_dealloc */
	0,                              /* (tp_print) */
	NULL,                           /* tp_getattr */
	NULL,                           /* tp_setattr */
	NULL,                           /* tp_compare */
	NULL,                           /* tp_repr */
	NULL,                           /* tp_as_number */
	NULL,                           /* tp_as_sequence */
	NULL,                           /* tp_as_mapping */
	NULL,                           /* tp_hash */
	NULL,                           /* tp_call */
	NULL,                           /* tp_str */
	NULL,                           /* tp_getattro */
	NULL,                           /* tp_setattro */
	NULL,                           /* tp_as_buffer */
	Py_TPFLAGS_BASETYPE|            /* tp_flags */
	Py_TPFLAGS_DEFAULT,
	NULL,                           /* tp_doc */
	NULL,                           /* tp_traverse */
	NULL,                           /* tp_clear */
	NULL,                           /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	NULL,                           /* tp_iter */
	NULL,                           /* tp_iternext */
	clockwork_methods,              /* tp_methods */
	clockwork_members,              /* tp_members */
	NULL,                           /* tp_getset */
	NULL,                           /* tp_base */
	NULL,                           /* tp_dict */
	NULL,                           /* tp_descr_get */
	NULL,                           /* tp_descr_set */
	0,                              /* tp_dictoffset */
	NULL,                           /* tp_init */
	NULL,                           /* tp_alloc */
	clockwork_new,                  /* tp_new */
};

#define ClockType(NAME) \
	NAME##ClockType = { \
		PyVarObject_HEAD_INIT(NULL, 0) \
		.tp_name = PYTHON_MODULE_PATH(#NAME), \
		.tp_basicsize = sizeof(struct Clockwork), \
		.tp_base = &ClockworkType, \
		.tp_flags = Py_TPFLAGS_DEFAULT, \
		.tp_methods = NULL, \
		.tp_new = NAME##_new \
	}

#define Clocks(...) \
	CLOCK_RECORD(Real, LOCAL_REAL_CLOCK_ID) \
	CLOCK_RECORD(Monotonic, LOCAL_MONOTONIC_CLOCK_ID)

static PyObj
Real_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {NULL};
	Clockwork cw;
	PyObj rob;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "", kwlist))
		return(NULL);

	rob = PyAllocate(subtype);
	if (rob == NULL)
		return(NULL);

	cw = (Clockwork) rob;
	cw->cw_clockid = LOCAL_REAL_CLOCK_ID;
	cw->cw_offset = 0;

	return(rob);
}

static PyObj
Monotonic_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {NULL};
	Clockwork cw;
	PyObj rob;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "", kwlist))
		return(NULL);

	rob = PyAllocate(subtype);
	if (rob == NULL)
		return(NULL);

	cw = (Clockwork) rob;
	cw->cw_clockid = LOCAL_MONOTONIC_CLOCK_ID;
	cw->cw_offset = 0;

	return(rob);
}

/**
	// Declare types.
*/
#define CLOCK_RECORD(NAME, CLOCK_ID) static PyTypeObject ClockType(NAME);
	Clocks()
#undef CLOCK_RECORD

#define PYTHON_TYPES() \
	ID(Clockwork, Clockwork) \
	ID(Real, RealClock) \
	ID(Monotonic, MonotonicClock)

#define MODULE_FUNCTIONS()
#include <fault/metrics.h>
#include <fault/python/module.h>
INIT(module, 0, NULL)
{
	#define ID(NAME, TYPNAME) \
		if (PyType_Ready((PyTypeObject *) &( TYPNAME##Type ))) \
			goto error; \
		Py_INCREF((PyObj) &( TYPNAME##Type )); \
		if (PyModule_AddObject(module, #NAME, (PyObj) &( TYPNAME##Type )) < 0) \
			{ Py_DECREF((PyObj) &( TYPNAME##Type )); goto error; }
		PYTHON_TYPES()
	#undef ID

	return(0);

	error:
	{
		return(-1);
	}
}
