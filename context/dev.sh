#!/bin/sh
# Command size reduction interface for fault.development.bin.*
# Provides abstraction for FPI_MECHANISMS.
NL='
'
FAULT_DIRECTORY="${FAULT_DIRECTORY:-"$HOME/.fault"}"
DEV="$FAULT_DIRECTORY/dev"
FPI="$FAULT_DIRECTORY/fpi"
SF="$FAULT_DIRECTORY/dev/projects.nll"
export FAULT_DIRECTORY

test -d "$DEV" || mkdir -p "$DEV"
cat "$SF" >/dev/null 2>/dev/null || touch "$SF"

PYTHON="${PYTHON:-$(which python3)}"
export PYTHON

FAULT_CONTEXT_NAME="${FAULT_CONTEXT_NAME:-fault}"
FAULT_DEVELOPMENT_PREFIX="${FAULT_DEVELOPMENT_PREFIX:-${FAULT_CONTEXT_NAME}.development.bin.}"

DEVCTX="${DEVCTX:-host:optimal}"
DEV_NAME="${DEVCTX%:*}"
DEV_PURPOSE="${DEVCTX#*:}"

gray () {
	echo >&2 "[38;5;240m""$@""[0m"
}
igray () {
	echo "[38;5;240m""$@""[0m"
}

QUIET=0
for opt
do
	case "$opt"
	in
		-q)
			QUIET=1
			shift
		;;

		-R)
			FPI_REBUILD=1
			export FPI_REBUILD
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

		-g)
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

		-h)
			echo >&2 "Usage: dev [-OMdt] [-HW] $(igray $FAULT_DEVELOPMENT_PREFIX)<command> factors ..."
			exit 64
		;;
		-*)
			echo >&2 "ERROR: unknown option '$opt'"
			exit 64
		;;

		*)
			break
		;;

		--)
			shift
			break
		;;
	esac
done

main="$FAULT_DIRECTORY/fpi/$DEV_NAME/${DEV_PURPOSE}.xml"
static="$FAULT_DIRECTORY/fpi/static/${DEV_PURPOSE}.xml"
FPI_MECHANISMS=$main:$static
export FPI_MECHANISMS

# Current setup.
DEVCTX="${DEV_NAME}:${DEV_PURPOSE}"
export DEVCTX

command="$1"
shift 1

if test $QUIET -eq 0
then
	echo >&2 "[38;5;240m[ Environment ]"
	echo >&2 "/script"
	echo >&2 "	\`$0\`"
	echo >&2 "/context"
	echo >&2 "	\`$DEVCTX\`"
	echo >&2 "/mechanisms"
	echo >&2 "	\`$FPI_MECHANISMS\`"
	echo >&2 "/paths"
	echo >&2 "	\`$DEVPATH\`"
	if test "${FPI_REBUILD:-0}" -eq 1
	then
		echo >&2 "/rebuild"
		echo >&2 "	\`enabled\`"
	fi
	printf >&2 "[0m"
fi

list_projects ()
{
	echo
	gray "[ Projects ]"

	IFS="$NL"
	for x in $(cat "$SF")
	do
		echo '	#' $x
	done
}

PYTHONPATH="$DEVPATH:$PYTHONPATH"
export PYTHONPATH

SF="$FAULT_DIRECTORY/dev/projects.nll"
case "$command"
in
	source)
		. "$@"
		exit
	;;

	ls)
		list_projects
	;;

	rm)
		for x
		do
			ns="$(grep -v "$x" "$SF")"
			echo "$ns" >"$SF"
			gray '-' "$x"
		done
		list_projects
	;;

	# Clear focus/projects.
	clear)
		echo "" >"$SF"
	;;

	add)
		for x
		do
			echo "$x" >> "$SF"
		done

		ns="$(cat "$SF" | sort | uniq)"
		echo "$ns" >"$SF"

		list_projects
	;;

	set)
		IFS="$NL"
		echo $* >> "$SF"
		list_projects
	;;

	setup)
		exec "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}setup"
	;;

	report)
		if test $# -eq 0
		then
			IFS="$NL"
			set -- $(cat "$SF")
			unset IFS
		fi

		emit_fails ()
		{
			for fail
			do
				test -d "$fail" || continue
				cd "$fail" 2>/dev/null || continue
				for x in ./*
				do
					gray '>>>>>>>>>>>>>'
					echo "$x"
					echo
					cat "$x"
				done
			done
		}

		for project
		do
			ft="$("$PYTHON" -c "import $project as x; print(getattr(x,'__factor_type__'))")"

			if test x"$ft" = x"context"
			then
				spfails="$("$PYTHON" -c "$(echo \
					"import ${FAULT_CONTEXT_NAME}.routes.library as r; " \
					"import $project as x; " \
					"print('\\\\n'.join(str(x.directory()/'__pycache__'/'failures') for x in r.Import.from_module(x).subnodes()[0]))"
				)")"
				IFS="$NL"
				emit_fails $spfails
				unset IFS
			else
				fails="$("$PYTHON" -c "$(echo \
					"import ${FAULT_CONTEXT_NAME}.routes.library as r; " \
					"import $project as x; " \
					"print(str(r.Import.from_module(x).directory()/'__pycache__'/'failures'))"
				)")"

				emit_fails "$fails"
			fi
			echo

			gray '<<<<<<<<<<'
		done 2>&1 | eval ${PAGER:-less -R}
	;;

	update|up)
		# Construct and Induct
		if test $# -eq 0
		then
			IFS="$NL"
			set -- $(cat "$SF")
		fi

		printf "{construct && induct}"
		gray " ""$@"
		"$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}construct" "$@" || exit
		exec "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}induct" "$@"
	;;

	switch)
		# Construct and Induct
		if test $# -eq 0
		then
			IFS="$NL"
			set -- $(cat "$SF")
		fi

		printf "{[switch] construct && -R induct}"
		gray " ""$@"
		"$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}construct" "$@" || exit

		# Switches need to rebuild on induct as modification times may
		# not be consistent across builds.
		FPI_REBUILD=1
		export FPI_REBUILD
		exec "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}induct" "$@"
	;;

	void)
		echo must be ran directly
		exit 64
	;;

	env)
		exec env "$@"
	;;

	'')
		list_projects
		echo
		exit 64
	;;

	*)
		if test $QUIET -eq 0
		then
			echo
		fi

		if test $# -eq 0
		then
			IFS="$NL"
			set -- $(cat "$SF")
		fi

		printf "$command"
		gray " ""$@"
		exec "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}$command" "$@"
	;;
esac
