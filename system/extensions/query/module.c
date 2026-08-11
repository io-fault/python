/**
	// Bindings for &system.intrinsics.query.
*/
#ifdef __linux__
	#define _GNU_SOURCE
#endif

#include <errno.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/utsname.h>

#include <fault/libc.h>
#include <fault/internal.h>
#include <fault/python/environ.h>

#ifndef FAULT_BOOTSTRAP
	#include <fault/query.h>
#else
	#include <fault/intrinsics/query.c>
#endif

#define ProcessMetrics_Recast(OB) PyObject_Recast(ProcessMetrics, OB)
#define ProcessMetrics_Record(OB) &(OB->pm_record)
#define ProcessMetrics_BinaryContext(R, S, O) \
	process_metrics_t * R##_r = ProcessMetrics_Record(ProcessMetrics_Recast(R)); \
	process_metrics_t * S##_r = ProcessMetrics_Record(ProcessMetrics_Recast(S)); \
	process_metrics_t * O##_r = ProcessMetrics_Record(ProcessMetrics_Recast(O));

#define pm_record_offset offsetof(struct ProcessMetricsObject, pm_record)

PyTypeObject ProcessMetricsType;
struct ProcessMetricsObject {
	PyObject_HEAD
	process_metrics_t pm_record;
};

typedef struct ProcessMetricsObject *ProcessMetrics;

STATIC(PyObj)
pm_processing_time(PyObj self)
{
	process_metrics_t *pmr = ProcessMetrics_Record(ProcessMetrics_Recast(self));
	pmetric_time_t time = pmr->total_user_time + pmr->total_system_time;

	return(PyFloat_FromDouble(time));
}

STATIC(PyObj)
pm_from_parts(PyTypeObject *typ, PyObj args, PyObj kw)
{
	process_metrics_t pm = {0,};
	PyObj rob;

	static const char *kwlist[] = {
		#define PMA(TYP, NAME) #NAME,
			ProcessMetricsParameters(PMA, (const char *), (const char *), (const char *))
		#undef PMA
		NULL
	};
	const char *const argtypes = "|"
		#define PMA(TYP, NAME) TYP
			ProcessMetricsParameters(PMA, "k", "d", "d")
		#undef PMA
	;

	#define PMA(TYP, NAME) , &pm.NAME
	#define storage ProcessMetricsParameters(PMA, X, Y, Z)
		if (!PyArg_ParseTupleAndKeywords(args, kw, argtypes, kwlist storage))
			return(NULL);
	#undef storage
	#undef PMA

	rob = typ->tp_alloc(typ, 0);
	if (rob != NULL)
	{
		process_metrics_t *pmr = ProcessMetrics_Record(ProcessMetrics_Recast(rob));
		memcpy(pmr, &pm, sizeof(process_metrics_t));
	}

	return(rob);
}

#define PyMethod_Id(N) pm_##N
STATIC(PyMethodDef)
pm_methods[] = {
	PyMethod_None(processing_time),
	#define PyMethod_TypeControl PyMethod_ClassType
		PyMethod_Keywords(from_parts),
	#define PyMethod_TypeControl PyMethod_InstanceType
	{NULL,},
};
#undef PyMethod_Id

STATIC(PyObj)
pm_add(PyObj self, PyObj operand)
{
	PyObj rob = NULL;

	if (!PyObject_IsInstance(operand, &ProcessMetricsType))
		PyErr_SetString(PyExc_TypeError, "operand is not a ProcessMetrics instance");
	else
	{
		rob = Py_TYPE(self)->tp_alloc(Py_TYPE(self), 0);
		if (rob != NULL)
		{
			ProcessMetrics_BinaryContext(rob, self, operand);
			process_metrics_combine(rob_r, (process_metrics_t *[]){self_r, operand_r, NULL});
		}
	}

	return(rob);
}

STATIC(PyNumberMethods)
pm_number_methods = {
	.nb_add = pm_add,
};

STATIC(PyObj)
pm_richcompare(PyObj self, PyObj operand, int cmpop)
{
	if (cmpop != Py_EQ)
		Py_RETURN_NOTIMPLEMENTED;

	if (self == operand)
		Py_RETURN_TRUE;

	if (Py_TYPE(operand) == (&ProcessMetricsType))
	{
		process_metrics_t *pm1, *pm2;

		pm1 = ProcessMetrics_Record(ProcessMetrics_Recast(self));
		pm2 = ProcessMetrics_Record(ProcessMetrics_Recast(operand));
		if (memcmp(pm1, pm2, sizeof(process_metrics_t)) == 0)
		{
			Py_RETURN_TRUE;
		}
	}

	Py_RETURN_FALSE;
}

STATIC(PyObj)
pm_str(PyObj self)
{
	char buf[2048];
	process_metrics_t *pmr = ProcessMetrics_Record(ProcessMetrics_Recast(self));
	PyObj rob;
	char *fmt =
		#define PMA(TYP, NAME) "\n\t" #NAME ": %" TYP
			ProcessMetricsParameters(PMA, "lu", "g", "g")
		#undef PMA
	;

	#define PMA(TYP, NAME) , pmr->NAME
	#define names ProcessMetricsParameters(PMA, X, Y, Z)
	snprintf(buf, sizeof(buf), fmt names);
	#undef names
	#undef PMA
	return(PyUnicode_FromFormat("[ProcessMetrics]:%s", buf));
}

STATIC(PyObj)
pm_repr(PyObj self)
{
	char buf[2048];
	process_metrics_t *pmr = ProcessMetrics_Record(ProcessMetrics_Recast(self));
	PyObj rob;
	char *fmt =
		#define PMA(TYP, NAME) ", " #NAME "=%" TYP
			ProcessMetricsParameters(PMA, "lu", "g", "g")
		#undef PMA
	;
	fmt += 2;

	#define PMA(TYP, NAME) , pmr->NAME
	#define names ProcessMetricsParameters(PMA, X, Y, Z)
	snprintf(buf, sizeof(buf), fmt names);
	#undef names
	#undef PMA
	return(PyUnicode_FromFormat("%s.from_parts(%s)", Py_TYPE(self)->tp_name, buf));
}

STATIC(PyObj)
pm_new(PyTypeObject *typ, PyObj args, PyObj kw)
{
	process_metrics_t *src;
	PyObj so = NULL, rob;
	static const char *kwlist[] = {"source", NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kw, "|O!", kwlist, &ProcessMetricsType, &so))
		return(NULL);

	rob = typ->tp_alloc(typ, 0);
	if (rob != NULL)
	{
		process_metrics_t *pmr = ProcessMetrics_Record(ProcessMetrics_Recast(rob));
		if (so != NULL)
		{
			src = ProcessMetrics_Record(ProcessMetrics_Recast(so));
			memcpy(pmr, src, sizeof(process_metrics_t));
		}
		else
			memset(pmr, 0, sizeof(process_metrics_t));
	}

	return(rob);
}

STATIC(PyMemberDef)
pm_members[] = {
	#define PMM(TYP, NAME) \
		{#NAME, Py_MEMBER_TYPE(ProcessMetrics_Field(NAME)), \
			pm_record_offset + offsetof(process_metrics_t, NAME), 0, NULL},

		ProcessMetricsParameters(PMM, T_UINT, T_DOUBLE, T_DOUBLE)
	#undef PMM
	NULL
};

CONCEAL(PyTypeObject)
ProcessMetricsType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	.tp_name = FACTOR_PATH("ProcessMetrics"),
	.tp_basicsize = sizeof(struct ProcessMetricsObject),
	.tp_itemsize = 0,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = pm_methods,
	.tp_members = pm_members,
	.tp_richcompare = pm_richcompare,
	.tp_new = pm_new,
	.tp_repr = pm_repr,
	.tp_str = pm_str,
	.tp_as_number = &pm_number_methods,
};

CONCEAL(PyObj)
pm_from_record(PyTypeObject *typ, process_metrics_t *record)
{
	PyObj rob;
	process_metrics_t *pmr;

	rob = typ->tp_alloc(typ, 0);
	if (rob == NULL)
		return(NULL);

	pmr = ProcessMetrics_Record(ProcessMetrics_Recast(rob));
	memcpy(pmr, record, sizeof(process_metrics_t));
	return(rob);
}

/**
	// Scans the process tree for resource usage data.
*/
CONCEAL(PyObj)
sq_process_usage_scan(PyObj mod, PyObj args)
{
	pid_t pid = 0;
	process_metrics_t m = {0,};
	long long p = 0;
	long long limit = 64;

	if (!PyArg_ParseTuple(args, "L|L", &p, &limit))
		return(NULL);

	process_usage_scan(&m, (pid_t) p, limit);
	return(pm_from_record(&ProcessMetricsType, &m));
}

CONCEAL(PyObj)
sq_process_executable_path(PyObj mod, PyObj args)
{
	unsigned long long pid = 0;
	char buf[1000*10];

	if (!PyArg_ParseTuple(args, "K", &pid))
		return(NULL);

	if (process_executable_path(buf, sizeof(buf), pid) > 0)
		return(Py_NEW_VALUE(buf));

	return(Py_NEW_VALUE(""));
}

static PyObj
sq_hostname(PyObj mod)
{
	char buf[512];
	int r;

	r = gethostname(buf, 512);
	if (r != 0)
	{
		PyErr_SetFromErrno(PyExc_OSError);
		return(NULL);
	}
	buf[511] = '\0';

	return(Py_NEW_VALUE(buf));
}

static PyObj
sq_machine(PyObj mod)
{
	PyObj rob;
	struct utsname un;
	int i;

	if (uname(&un) != 0)
	{
		return(NULL);
	}

	i = 0;
	while (un.sysname[i])
	{
		un.sysname[i] = tolower(un.sysname[i]);
		++i;
	}

	i = 0;
	while (un.machine[i])
	{
		un.machine[i] = tolower(un.machine[i]);
		++i;
	}

	rob = Py_BuildValue("ss", un.sysname, un.machine);
	return(rob);
}

static PyObj
sq_clock_ticks(PyObj mod)
{
	int r;
	r = sysconf(_SC_CLK_TCK);
	return(PyLong_FromLong((long) r));
}

#define PYTHON_TYPES() \
	ID(ProcessMetrics)

PyObj sq_process_usage_scan(PyObj, PyObj);
PyObj sq_process_executable_path(PyObj, PyObj);

#define PyMethod_Id(N) sq_##N
#define MODULE_FUNCTIONS() \
	PyMethod_Variable(process_usage_scan), \
	PyMethod_Variable(process_executable_path), \
	PyMethod_None(hostname), \
	PyMethod_None(machine), \
	PyMethod_None(clock_ticks), \

#include <fault/metrics.h>
#include <fault/python/module.h>
INIT(module, 0, NULL)
{
	#define ID(NAME) \
		if (PyType_Ready((PyTypeObject *) &( NAME##Type ))) \
			goto error; \
		Py_INCREF((PyObj) &( NAME##Type )); \
		if (PyModule_AddObject(module, #NAME, (PyObj) &( NAME##Type )) < 0) \
			{ Py_DECREF((PyObj) &( NAME##Type )); goto error; }
		PYTHON_TYPES()
	#undef ID

	if (PyModule_AddStringConstant(module, "fv_architecture", FV_ARCHITECTURE_STR))
		goto error;
	if (PyModule_AddStringConstant(module, "fv_system", FV_SYSTEM_STR))
		goto error;

	if (PyModule_AddIntConstant(module, "machine_addressing", sizeof(void *) * 8))
		goto error;

	// While _query still exists.
	{
		PyObj g = PyModule_GetDict(module);
		PyObj xr;
		xr = PyRun_String("from ._query import *", Py_file_input, g, g);
		if (xr == NULL)
			goto error;
		Py_DECREF(xr);
	}
	return(0);

	error:
	{
		return(-1);
	}
}
#undef PyMethod_Id
