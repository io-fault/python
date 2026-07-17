/**
	// KernelQueue and TaskQueue based scheduler.
*/
#ifndef _SYSTEM_KERNEL_SCHEDULER_H_included_
#define _SYSTEM_KERNEL_SCHEDULER_H_included_

#define Scheduler_GetTaskQueue(EV) (&(EV->ks_tq))
#define Scheduler_GetKernelQueue(EV) (&(EV->ks_eq))

/**
	// Whether a wait (for events) call should use
	// a non-zero timeout when checking for kernel events.

	// Cancellations are of particular importance as Events
	// with file descriptors are closed when deleted. If
	// cancellations are not attended to immediately,
	// temporary hangs may occur for common pipe usage patterns
	// as the downstream receives a delayed EOF.
*/
#define Scheduler_ShouldWait(EV) ( \
	!(TQ_HAS_TASKS(Scheduler_GetTaskQueue(EV))) \
	&& (PyList_GET_SIZE(Scheduler_GetKernelQueue(EV)->kq_cancellations) == 0) \
)

#define Scheduler_GetExceptionTrap(EV) ((EV->ks_exc))
#define Scheduler_SetExceptionTrap(EV, OB) (Scheduler_GetExceptionTrap(EV) = OB)
#define Scheduler_UpdateExceptionTrap(EV, OB) do { \
	Py_XDECREF(Scheduler_GetExceptionTrap(EV)); \
	Scheduler_SetExceptionTrap(EV, OB); \
	Py_XINCREF(OB); \
} while(0)

typedef struct Scheduler *Scheduler;
struct Scheduler {
	PyObject_HEAD
	PyObj weakreflist;

	int ks_waiting;
	PyObj ks_exc;
	struct TaskQueue ks_tq;
	struct KernelQueue ks_eq;
};
#endif
