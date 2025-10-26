/**
	// system tty device interface

	// The functionality is purposefully incomplete and primarily intended for
	// use by terminal applications.
*/
#include <wchar.h>
#include <fcntl.h>
#include <unistd.h>

#include <fault/libc.h>
#include <fault/internal.h>
#include <fault/python/environ.h>

#include "tty.h"

static PyObj
fs_device(PyObj self)
{
	int fd = -1;
	char *name;

	if (isatty(STDERR_FILENO))
		fd = STDERR_FILENO;
	else if (isatty(STDIN_FILENO))
		fd = STDIN_FILENO;
	else if (isatty(STDOUT_FILENO))
		fd = STDOUT_FILENO;
	else
	{
		/* Set errno if unset. */
		if (errno != 0)
			errno = ENXIO;

		return(PyErr_SetFromErrno(PyExc_OSError));
	}

	name = ttyname(fd);
	if (name == NULL)
		return(PyErr_SetFromErrno(PyExc_OSError));

	return(PyUnicode_FromString(name));
}

static PyObj
device_set_controlling_process(PyObj self, PyObj ob)
{
	Device dev = (Device) self;
	long pgid;

	pgid = PyLong_AsLong(ob);
	if (PyErr_Occurred())
		return(NULL);

	if (tcsetpgrp(dev->dev_fd, (pid_t) pgid))
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_RETURN_NONE;
}

static PyObj
device_get_controlling_process(PyObj self)
{
	Device dev = (Device) self;
	pid_t pgid;

	pgid = tcgetpgrp(dev->dev_fd);
	if (pgid == -1)
		return(PyErr_SetFromErrno(PyExc_OSError));

	return(PyLong_FromLong((long) pgid));
}

static PyObj
device_get_window_dimensions(PyObj self)
{
	int r;
	Device dev = (Device) self;
	struct winsize ws;
	PyObj rob, h, v;

	_PY_THREAD_SUSPEND_
	r = ioctl((int) dev->dev_fd, TIOCGWINSZ, &ws);
	_PY_THREAD_RESUME_

	if (r)
		return(PyErr_SetFromErrno(PyExc_OSError));

	h = PyLong_FromLong(ws.ws_col);
	if (h == NULL)
		return(NULL);
	v = PyLong_FromLong(ws.ws_row);
	if (v == NULL)
		goto herror;

	rob = PyTuple_New(2);
	if (rob == NULL)
		goto error;

	PyTuple_SET_ITEM(rob, 0, h);
	PyTuple_SET_ITEM(rob, 1, v);

	return(rob);

	error:
		Py_DECREF(v);
	herror:
		Py_DECREF(h);

	return(NULL);
}

static PyObj
device_fs_path(PyObj self)
{
	Device dev = (Device) self;
	char *path = ttyname(dev->dev_fd);

	if (path == NULL)
	{
		PyErr_SetFromErrno(PyExc_OSError);
		return(NULL);
	}

	return(PyUnicode_FromString(path));
}

static PyObj
device_send_break(PyObj self, PyObj args)
{
	Device dev = (Device) self;
	int duration = 0;

	if (!PyArg_ParseTuple(args, "|i", &duration))
		return(NULL);

	if (tcsendbreak(dev->dev_fd, duration) != 0)
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_drain(PyObj self)
{
	Device dev = (Device) self;

	if (tcdrain(dev->dev_fd) != 0)
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_record(PyObj self)
{
	Device dev = (Device) self;

	if (tcgetattr(dev->dev_fd, &(dev->dev_ts)) == -1)
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_restore(PyObj self)
{
	Device dev = (Device) self;

	if (tcsetattr(dev->dev_fd, TCSAFLUSH, &(dev->dev_ts)) == -1)
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_set_message_limits(PyObj self, PyObj args)
{
	Device dev = (Device) self;
	struct termios ts;
	unsigned char vmin, vtime;

	if (!PyArg_ParseTuple(args, "bb", &vmin, &vtime))
		return(NULL);

	if (tcgetattr(dev->dev_fd, &ts) == -1)
		return(PyErr_SetFromErrno(PyExc_OSError));

	ts.c_cc[VMIN] = vmin;
	ts.c_cc[VTIME] = vtime;

	if (tcsetattr(dev->dev_fd, TCSAFLUSH, &ts))
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_set_raw(PyObj self)
{
	Device dev = (Device) self;
	struct termios ts;

	if (tcgetattr(dev->dev_fd, &ts) == -1)
		return(PyErr_SetFromErrno(PyExc_OSError));

	ts.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
	ts.c_oflag &= ~OPOST;
	ts.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
	ts.c_cflag &= ~(CSIZE | PARENB);
	ts.c_cflag |= CS8;
	ts.c_cc[VMIN] = 1;
	ts.c_cc[VTIME] = 0;

	if (tcsetattr(dev->dev_fd, TCSAFLUSH, &ts))
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_set_cbreak(PyObj self)
{
	Device dev = (Device) self;
	struct termios ts;

	if (tcgetattr(dev->dev_fd, &ts) == -1)
		return(PyErr_SetFromErrno(PyExc_OSError));

	ts.c_lflag &= ~(ECHO | ICANON);
	ts.c_cc[VMIN] = 1;
	ts.c_cc[VTIME] = 0;

	if (tcsetattr(dev->dev_fd, TCSAFLUSH, &ts))
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_set_cooked(PyObj self)
{
	Device dev = (Device) self;
	struct termios ts = {0,};

	/**
		// Retrieve settings snapshot for existing keybinds in c_cc.
		// This function is not looking to implement a total
		// reset as it's not expected to perform that kind of cleanup.
	*/
	if (tcgetattr(dev->dev_fd, &ts) == -1)
		return(PyErr_SetFromErrno(PyExc_OSError));

	#ifndef IMAXBEL
		#define IMAXBEL 0
	#endif
	#ifndef ECHOCTL
		#define ECHOCTL 0
	#endif

	ts.c_iflag = (BRKINT| ICRNL| IMAXBEL | IXON | IXANY);
	ts.c_oflag = (OPOST | ONLCR);
	ts.c_lflag = (ICANON | ISIG | IEXTEN | ECHO | ECHOE | ECHOKE | ECHOCTL);
	ts.c_cflag = (CREAD | CS8 | HUPCL);
	ts.c_ispeed = B9600;
	ts.c_ospeed = B9600;
	ts.c_cc[VMIN] = 1;
	ts.c_cc[VTIME] = 0;

	if (tcsetattr(dev->dev_fd, TCSAFLUSH, &ts))
		return(PyErr_SetFromErrno(PyExc_OSError));

	Py_INCREF(self);
	return(self);
}

static PyObj
device_open(PyObj subtype, PyObj args)
{
	PyObj bytespath = NULL;
	Device dev;
	PyObj rob;

	if (!PyArg_ParseTuple(args, "|O&", PyUnicode_FSConverter, &bytespath))
		return(NULL);

	rob = PyAllocate(subtype);
	if (rob == NULL)
	{
		Py_XDECREF(bytespath);
		return(NULL);
	}

	dev = (Device) rob;
	if (bytespath != NULL)
	{
		dev->dev_fd = open(PyBytes_AS_STRING(bytespath), O_CLOEXEC|O_RDWR);
		Py_DECREF(bytespath);
	}
	else
		dev->dev_fd = open(SYSTEM_TTY_DEVICE_PATH, O_CLOEXEC|O_RDWR);

	if (dev->dev_fd == -1)
	{
		Py_DECREF(rob);
		return(PyErr_SetFromErrno(PyExc_OSError));
	}

	return(rob);
}

static PyObj
device_fileno(PyObj self)
{
	Device dev = (Device) self;
	return PyLong_FromLong((long) dev->dev_fd);
}

static PyMethodDef
device_methods[] = {
	{"open", (PyCFunction) device_open, METH_VARARGS|METH_CLASS, NULL},
	{"fileno", (PyCFunction) device_fileno, METH_NOARGS, NULL},
	{"fs_path", (PyCFunction) device_fs_path, METH_NOARGS, NULL},

	{"set_controlling_process", (PyCFunction) device_set_controlling_process, METH_O, NULL},
	{"get_controlling_process", (PyCFunction) device_get_controlling_process, METH_NOARGS, NULL},

	{"get_window_dimensions", (PyCFunction) device_get_window_dimensions, METH_NOARGS, NULL},

	{"record", (PyCFunction) device_record, METH_NOARGS, NULL},
	{"restore", (PyCFunction) device_restore, METH_NOARGS, NULL},

	{"send_break", (PyCFunction) device_send_break, METH_VARARGS, NULL},
	{"drain", (PyCFunction) device_drain, METH_NOARGS, NULL},

	{"set_message_limits", (PyCFunction) device_set_message_limits, METH_VARARGS, NULL},

	{"set_raw", (PyCFunction) device_set_raw, METH_NOARGS, NULL},
	{"set_cbreak", (PyCFunction) device_set_cbreak, METH_NOARGS, NULL},
	{"set_cooked", (PyCFunction) device_set_cooked, METH_NOARGS, NULL},
	{NULL},
};

static PyMemberDef
device_members[] = {
	{"kport", T_INT, offsetof(struct Device, dev_fd), READONLY, NULL},
	{NULL},
};

static PyObj
device_new(PyTypeObject *subtype, PyObj args, PyObj kw)
{
	static char *kwlist[] = {"fd", NULL};
	long fd;
	Device dev;
	PyObj rob;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "l", kwlist, &fd))
		return(NULL);

	rob = PyAllocate(subtype);
	if (rob == NULL)
		return(NULL);

	dev = (Device) rob;
	dev->dev_fd = fd;
	return(rob);
}

static PyTypeObject
DeviceType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	PYTHON_MODULE_PATH("Device"),   /* tp_name */
	sizeof(struct Device),          /* tp_basicsize */
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
	Py_TPFLAGS_BASETYPE|
	Py_TPFLAGS_DEFAULT,             /* tp_flags */
	NULL,                           /* tp_doc */
	NULL,                           /* tp_traverse */
	NULL,                           /* tp_clear */
	NULL,                           /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	NULL,                           /* tp_iter */
	NULL,                           /* tp_iternext */
	device_methods,                 /* tp_methods */
	device_members,                 /* tp_members */
	NULL,                           /* tp_getset */
	NULL,                           /* tp_base */
	NULL,                           /* tp_dict */
	NULL,                           /* tp_descr_get */
	NULL,                           /* tp_descr_set */
	0,                              /* tp_dictoffset */
	NULL,                           /* tp_init */
	NULL,                           /* tp_alloc */
	device_new,                     /* tp_new */
};

#define PYTHON_TYPES() \
	ID(Device)

#define MODULE_FUNCTIONS() \
	PYMETHOD(fs_device, fs_device, METH_NOARGS, NULL)

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

	return(0);

	error:
	{
		return(-1);
	}
}
