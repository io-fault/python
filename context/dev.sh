#!/bin/sh
FAULT_DIRECTORY="${FAULT_DIRECTORY:-"$HOME/.fault"}"
export FAULT_DIRECTORY

PYTHON="${PYTHON:-$(which python3)}"
export PYTHON

FAULT_DEVELOPMENT_PREFIX="${FAULT_DEVELOPMENT_PREFIX:-fault.development.bin.}"

DEV_PURPOSE=optimal
DEV_NAME=host

QUIET=0
OPTIONS=`getopt qOdtMHW "$@"`; OPTERROR=$?; set -- $OPTIONS
if test $OPTERROR -ne 0
then
	echo >&2 "Usage: dev [-OMdt] [-HW] <[fault.development.bin.]command> factors ..."
	exit 64 # EX_USAGE
fi

for opt
do
	case "$opt"
	in
		-q)
			QUIET=1
			shift
		;;
		# Explicit purpose
		-P)
			shift; DEV_PURPOSE="$1"
			shift
		;;

		-O)
			DEV_PURPOSE='optimal'
			shift
		;;
		-d)
			DEV_PURPOSE='debug'
			shift
		;;
		-t)
			DEV_PURPOSE='test'
			shift
		;;
		-M)
			DEV_PURPOSE='metrics'
			shift
		;;

		-X)
			shift; DEV_NAME="$1"
			shift
		;;

		-H)
			DEV_NAME=host
			shift
		;;
		-W)
			DEV_NAME=web
			shift
		;;

		--)
			shift
			break
		;;
	esac
done

main="$FAULT_DIRECTORY/dev/$DEV_NAME/$DEV_PURPOSE"
static="$FAULT_DIRECTORY/dev/static/$DEV_PURPOSE"
FPI_MECHANISMS=$main:$static
export FPI_MECHANISMS

# Current setup.
FPI_PURPOSE=$DEV_PURPOSE
FPI_CONTEXT=$DEV_NAME
export FPI_PURPOSE
export FPI_CONTEXT

DEV_CONTEXT="${DEV_NAME}:${DEV_PURPOSE}"
export DEV_CONTEXT

command="$1"
shift 1

if test $QUIET -eq 0
then
	echo >&2 "[38;5;240m[ Environment ]"
	echo >&2 "/context"
	echo >&2 "	\`$DEV_CONTEXT\`"
	echo >&2 "/mechanisms"
	echo >&2 "	\`$FPI_MECHANISMS\`"
	printf >&2 "[0m"
fi

case "$command"
in
	source)
		. "$@"
		exit
	;;
	env)
		exec env "$@"
	;;
	'')
		exec env
	;;
	*)
		exec "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}$command" "$@"
	;;
esac
