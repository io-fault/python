#!/bin/sh
# Command size reduction interface for fault.development.bin.*
# Provides abstraction for FPI_MECHANISMS and higher level commands.

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
DEV_INTENTION="${DEVCTX#*:}"
DEV_INTENTION_SELECTED=0

gray () {
	echo >&2 "[38;5;240m""$@""[0m"
}
igray () {
	echo "[38;5;240m""$@""[0m"
}

QUIET=0
DONE=0
while test $DONE -eq 0
do
	RESTART=0

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

			# Explicit intention
			-P)
				shift; DEV_INTENTION="$1"
				shift
			;;

			-O)
				DEV_INTENTION='optimal'
				DEV_INTENTION_SELECTED=1
				shift
			;;

			-g)
				DEV_INTENTION='debug'
				DEV_INTENTION_SELECTED=1
				shift
			;;

			-t)
				DEV_INTENTION='test'
				DEV_INTENTION_SELECTED=1
				shift
			;;

			-M)
				DEV_INTENTION='metrics'
				DEV_INTENTION_SELECTED=1
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

			-I)
				DEV_NAME=inspect
				shift
			;;

			-W)
				DEV_NAME=web
				shift
			;;

			-h)
				echo >&2 "Usage: dev [-OMIdt] [-HW] $(igray $FAULT_DEVELOPMENT_PREFIX)<command> factors ..."
				exit 64
			;;

			--)
				shift
				break
			;;

			--*)
				echo >&2 "ERROR: unknown option '$opt'"
				exit 64
			;;

			-*)
				shift

				if test $(echo $opt | wc -c) -gt 3
				then
					# Split the options and restart.
					# Python is expected, so avoid shell variant.
					# Presume that it will need to refresh the for loop.
					set -- $("$PYTHON" -c "x='$opt'; z=[print('-'+y) for y in x[1:]]") "$@"
					RESTART=1
					break
				else
					echo >&2 "ERROR: unknown option '$opt'"
					exit 64
				fi
			;;

			*)
				break
			;;
		esac
	done

	test $RESTART -eq 0 && DONE=1
done

if test x"$1" = x'measure'
then
	DEV_INTENTION='measure'
	if test $DEV_INTENTION_SELECTED -eq 0
	then
		echo >&2 'Ignored selected purpose `'"$DEV_INTENTION"'` for metrics; `measure` is required.'
	fi
elif test x"$1" = x"test"
then
	if test $DEV_INTENTION_SELECTED -eq 0
	then
		# Not explicitly selected, so use test for test.
		DEV_INTENTION='test'
	fi
else
	:
fi

if test x"$1" = x"iterate"
then
	unset FPI_MECHANISMS # Subprocess will init this.
	QUIET=1
else
	# Initialize environment for subprocesses.

	main="$FAULT_DIRECTORY/fpi/$DEV_NAME/${DEV_INTENTION}.xml"
	static="$FAULT_DIRECTORY/fpi/static/${DEV_INTENTION}.xml"
	FPI_MECHANISMS=$main:$static
	export FPI_MECHANISMS

	# Current config.
	DEVCTX="${DEV_NAME}:${DEV_INTENTION}"
	export DEVCTX
fi

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
	py|python)
		exec "$PYTHON" "$@"
	;;

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

	# Clear focus. (project list)
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
		# Read the failures from validate.

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

	reconstruct)
		# Construct with FPI_REBUILD=1
		if test $# -eq 0
		then
			IFS="$NL"
			set -- $(cat "$SF")
		fi

		printf "{reconstruct}"
		gray " ""$@"
		exec env FPI_REBUILD=1 time "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}construct" "$@"
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
		env time "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}construct" "$@" || exit
		exec env time "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}induct" "$@"
	;;

	switch)
		# Construct and Induct (with rebuild for induct)
		# The last modified times might be off for allowing a induct
		# to succeed without FPI_REBUILD=1.

		if test $# -eq 0
		then
			IFS="$NL"
			set -- $(cat "$SF")
		fi

		printf "{[switch] construct && -R induct}"
		gray " ""$@"
		env time "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}construct" "$@" || exit

		# Switches need to rebuild on induct as modification times may
		# not be consistent across builds.
		FPI_REBUILD=1
		export FPI_REBUILD
		exec env time "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}induct" "$@"
	;;

	iterate)
		state="$1"
		shift

		# inspect:metrics; Data extracted from ASTs or annotated structure.
		sh "$0" -MI construct "$@"

		# host:metrics; primary focus
		sh "$0" -MH switch "$@" # Easy access to binaries for extraction.

		: "$0" -Hi measure target-dir "$@"
		: "$0" -Hi execute fault.factors.bin.instantiate ...

		sh "$0" -OH switch "$@" && \
		sh "$0" -OH validate "$@"
	;;

	test)
		state="$1"
		shift

		if test $# -eq 0
		then
			IFS="$NL"
			set -- $(cat "$SF")
			unset IFS
		fi

		for x in "$@"
		do
			echo
			printf "$command"
			gray " $x"
			env time "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}test" "$x" || exit
		done
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
		exec env time "$PYTHON" -m "${FAULT_DEVELOPMENT_PREFIX}$command" "$@"
	;;
esac
