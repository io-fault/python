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

static PyObj
sq_executable_paths(PyObj mod)
{
	PyObj path_type, rob;
	path_vector_t *pv;

	path_type = PyImport_ImportAdjacent("files", "root");
	if (path_type == NULL)
		return(NULL);

	pv = executable_paths(NULL);

	rob = PyList_New(pv->path_count);
	if (rob == NULL)
		goto error;

	for (int i = 0; i < pv->path_count; ++i)
	{
		PyObj str = PyUnicode_DecodeFSDefaultAndSize(pv->path_strings[i], strlen(pv->path_strings[i]));
		PyObj path = NULL;

		if (str == NULL)
			goto error;

		path = PyObject_CallMethod(path_type, "__matmul__", "O", str);
		Py_DECREF(str);
		if (path == NULL)
			goto error;

		PyList_SET_ITEM(rob, i, path);
	}

	free(pv);
	Py_DECREF(path_type);
	return(rob);

	error:
	{
		free(pv);
		Py_DECREF(path_type);
		Py_XDECREF(rob);
		return(NULL);
	}
}

static PyObj
path_object(const char *path, size_t path_length)
{
	PyObj path_type, path_str, rob;

	path_type = PyImport_ImportAdjacent("files", "root");
	if (path_type == NULL)
		return(NULL);

	path_str = PyUnicode_DecodeFSDefaultAndSize(path, path_length);
	if (path_str == NULL)
	{
		Py_DECREF(path_type);
		return(NULL);
	}

	rob = PyObject_CallMethod(path_type, "__matmul__", "O", path_str);
	Py_DECREF(path_type);
	Py_DECREF(path_str);
	return(rob);
}

struct ExecutablePathIterator {
	PyObject_HEAD
	path_vector_t *paths;
	int index;
	char *buffer;
	size_t length;
	PyObj name;
};
typedef struct ExecutablePathIterator *EPI;
#define EPI_Recast(X) PyObject_Recast(EPI, X)

static void
epi_dealloc(PyObj self)
{
	EPI epi = EPI_Recast(self);

	if (epi->paths)
	{
		free(epi->paths);
		epi->paths = NULL;
	}

	if (epi->buffer)
	{
		free(epi->buffer);
		epi->buffer = NULL;
	}

	epi->length = 0;
	Py_CLEAR(epi->name);
}

static PyObj
epi_iter(PyObj self)
{
	Py_INCREF(self);
	return(self);
}

static PyObj
epi_iternext(PyObj self)
{
	int rindex;
	EPI epi = EPI_Recast(self);
	const char *exename = PyBytes_AS_STRING(epi->name);

	rindex = executable_scan(epi->buffer, epi->length, epi->paths, exename, epi->index);
	if (rindex == 0)
		return(NULL);

	epi->index = rindex;
	return(path_object(epi->buffer, strlen(epi->buffer)));
}

CONCEAL(PyTypeObject)
ExecutablePathIteratorType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	.tp_name = FACTOR_PATH("ExecutablePathIterator"),
	.tp_basicsize = sizeof(struct ExecutablePathIterator),
	.tp_itemsize = 0,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_dealloc = epi_dealloc,
	.tp_iter = epi_iter,
	.tp_iternext = epi_iternext,
};

static PyObj
sq_executables(PyObj module, PyObj name)
{
	EPI epi;
	PyObj rob;

	rob = ExecutablePathIteratorType.tp_alloc(&ExecutablePathIteratorType, 0);
	if (rob == NULL)
		return(NULL);

	epi = EPI_Recast(rob);
	epi->index = 0;

	epi->name = PyUnicode_EncodeFSDefault(name);
	if (epi->name == NULL)
		goto error;

	epi->paths = executable_paths(NULL);
	if (epi->paths == NULL)
	{
		PyErr_SetString(PyExc_MemoryError, "could not allocate memory for path vector");
		goto error;
	}

	// +2 for '\0' and '/'.
	epi->length = epi->paths->path_maximum_length + PyBytes_GET_SIZE(epi->name) + 2;
	epi->buffer = malloc(epi->length);
	if (epi->buffer == NULL)
	{
		PyErr_SetString(PyExc_MemoryError, "could not allocate memory for path buffer");
		goto error;
	}

	return(rob);
	error:
	{
		Py_DECREF(rob);
		return(NULL);
	}
}

static PyObj
sq_executable(PyObj module, PyObj name)
{
	const char *path;
	PyObj rob, name_bytes = PyUnicode_EncodeFSDefault(name);

	if (name_bytes == NULL)
		return(NULL);

	path = executable_first(PyBytes_AS_STRING(name_bytes));
	if (path == NULL)
		Py_RETURN_NONE;

	rob = path_object(path, strlen(path));
	free(path);
	return(rob);
}

enum UserField {
	uf_identifier = 0,
	uf_name,
	uf_title,
	uf_role,
	uf_shell,
	uf_home,
};
typedef enum UserField uf_t;

static PyObj
user_name(PyObj module)
{
	char *u_name = (char *) current_user_profile()->u_name;

	if (u_name[0] == '\0')
		Py_RETURN_NONE;
	return(Py_NEW_VALUE(u_name));
}

static PyObj
sq_username(PyObj module)
{
	char *u_name = getenv("USER");

	if (u_name != NULL && u_name[0] != '\0')
		return(Py_NEW_VALUE(u_name));

	return(user_name(module));
}

static PyObj
user_home(PyObj module)
{
	const char *u_home = current_user_profile()->u_home;

	if (u_home[0] == '\0')
		Py_RETURN_NONE;
	return(path_object(u_home, strlen(u_home)));
}

static PyObj
sq_home(PyObj module)
{
	const char *u_home = getenv("HOME");

	if (u_home != NULL && u_home[0] != '\0')
		return(path_object(u_home, strlen(u_home)));

	return(user_home(module));
}

static PyObj
user_role(PyObj module)
{
	char *u_role = (char *) current_user_profile()->u_role;

	if (u_role[0] == '\0')
		Py_RETURN_NONE;
	return(Py_NEW_VALUE(u_role));
}

static PyObj
user_title(PyObj module)
{
	char *u_title = (char *) current_user_profile()->u_title;

	if (u_title[0] == '\0')
		Py_RETURN_NONE;
	return(Py_NEW_VALUE(u_title));
}

static PyObj
user_shell(PyObj module)
{
	const char *u_shell = current_user_profile()->u_shell;

	if (u_shell[0] == '\0')
		Py_RETURN_NONE;
	return(path_object(u_shell, strlen(u_shell)));
}

static PyObj
sq_user(PyObj module, PyObj args, PyObj kw)
{
	int uid = -1;
	const char *field = NULL;
	const char *const kwlist[] = {
		"field", "identifier", NULL
	};
	uf_t uf;
	PyObj rob;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "|si", kwlist, &field, &uid))
		return(NULL);

	switch (uid)
	{
		case -1:
			uid = getuid();
		break;

		case -2:
			uid = geteuid();
		break;

		default:
			if (uid < 0)
			{
				PyErr_SetString(PyExc_ValueError, "invalid user identifier");
				return(NULL);
			}
		break;
	}

	// Return user identifier.
	if (field == NULL || strcmp("identifier", field) == 0)
		uf = uf_identifier;
	else if (strcmp("title", field) == 0)
		uf = uf_title;
	else if (strcmp("shell", field) == 0)
		uf = uf_shell;
	else if (strcmp("name", field) == 0)
		uf = uf_name;
	else if (strcmp("home", field) == 0)
		uf = uf_home;
	else
		uf = -1;

	switch (uf)
	{
		case uf_identifier:
			return(Py_NEW_VALUE(uid));
		break;

		case uf_name:
			rob = user_name(module);
		break;

		case uf_home:
			rob = user_home(module);
		break;

		case uf_shell:
			rob = user_shell(module);
		break;

		case uf_title:
			rob = user_title(module);
		break;

		case uf_role:
			rob = user_role(module);
		break;

		default:
		{
			rob = Py_None;
			Py_INCREF(rob);
		}
		break;
	}

	return(rob);
}

#define PYTHON_TYPES() \
	ID(ProcessMetrics) \
	ID(ExecutablePathIterator) \

PyObj sq_process_usage_scan(PyObj, PyObj);
PyObj sq_process_executable_path(PyObj, PyObj);

#define PyMethod_Id(N) sq_##N
#define MODULE_FUNCTIONS() \
	PyMethod_Variable(process_usage_scan), \
	PyMethod_Variable(process_executable_path), \
	\
	PyMethod_None(username), \
	PyMethod_None(home), \
	PyMethod_None(hostname), \
	PyMethod_None(machine), \
	PyMethod_None(clock_ticks), \
	\
	PyMethod_None(executable_paths), \
	PyMethod_Sole(executables), \
	PyMethod_Sole(executable), \
	\
	PyMethod_Keywords(user), \

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

	return(0);

	error:
	{
		return(-1);
	}
}
#undef PyMethod_Id
