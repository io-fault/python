#!/bin/sh
# Usage: sh fault/context/bootstrap.sh <fault-dir-path> <python3>
# Bootstrapping for fault.
# Creates the C modules that are needed to build

fault="$1"; shift 1
if ! test -d "$fault"
then
	echo >&2 "first parameter must be the 'fault' context package root directory."
	exit 1
fi

python="$(which "$1")"; shift 1
if ! test -x "$python"
then
	echo >&2 "second parameter must be the Python implementation to build for."
	exit 1
fi

SCD=`pwd`
if readlink "$python"
then
	cd "$(dirname "$python")"
	pylink="$(readlink "$python")"
	cd "$(dirname "$pylink")"
	cd ..
	prefix="$(pwd)"
else
	prefix="$(dirname "$(dirname "$python")")"
fi
cd "$SCD"
unset SCD

if test 1 = 2
then
	if test -e ./version:
	then
		VERSION="$(cat ./version)"
	else
		VERSION=0
	fi

	FAULT="http://fault.io/projects/python/?version="

	##
	# fetch, curl, wget.
	if which fetch >/dev/null 2>/dev/null
	then
		FETCH="$(which fetch)"
		fetch ()
		{
			out="$1"
			shift 1

			"$FETCH" -o "$out" "$@"
		}
	elif which curl >/dev/null 2>/dev/null
	then
		FETCH="$(which curl)"
		fetch ()
		{
			out="$1"
			shift 1

			"$FETCH" --insecure -f -L "$@" -o "$out"
		}
	elif which wget >/dev/null 2>/dev/null
	then
		FETCH="$(which wget)"
		fetch ()
		{
			out="$1"
			shift 1

			"$FETCH" -o "$out" "$@"
		}
	else
		echo >&2 "no fetch process found: expecting fetch, curl, or wget to be available"
		exit 3
	fi
fi

pyversion="$("$python" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
pyabi="$("$python" -c 'import sys; print(sys.abiflags)')"

test $? -eq 0 || exit 1

compile ()
{
	compiler="$1"; shift 1
	echo "$compiler" $osflags "$@"

	"$compiler" $osflags "$@"
}

platsuffix="so" # Following platform switch overrides when necessary.

case "$(uname -s)" in
	*Darwin*)
		osflags="-Wl,-bundle,-undefined,dynamic_lookup,-lSystem,-L$prefix/lib,-lpython$pyversion$pyabi -fPIC";
	;;
	*FreeBSD*)
		osflags="-Wl,-lc,-L$prefix/lib,-lpython$pyversion$pyabi -fPIC -shared -pthread"
	;;
	*)
		osflags="-Wl,-shared,--export-all-symbols,--export-dynamic,-lc,-lpthread,-L$prefix/lib,-lpython$pyversion$pyabi -fPIC"
	;;
esac

original="$(pwd)"

cd "$fault"
fault_dir="$(pwd)"
container_dir="$(dirname "$fault_dir")"
echo $container_dir

module_path ()
{
	dirpath="$1"
	shift 1

	relpath="$(echo "$dirpath" | sed "s:${container_dir}::")"
	echo "$relpath" | sed 's:/:.:g' | sed 's:.::'
}

for project in ./chronometry ./system ./development ./traffic ./io
do
	cd "$fault_dir/$project"
	root="$(dirname "$(pwd)")"

	if ! test -d ./extensions
	then
		cd "$original"
		continue
	fi

	for module in ./extensions/*/
	do
		iscache="$(echo "$module" | grep '__pycache__')"
		if ! test x"$iscache" = x""
		then
			continue
		fi

		cd "$module"
		modname="$(basename "$(pwd)")"

		fullname="$(module_path "$(pwd)")"
		targetname="$(echo "$fullname" | sed 's/.extensions//')"
		pkgname="$(echo "$fullname" | sed 's/[.][^.]*$//')"

		compile ${CC:-cc} -v -o "../../${modname}.${platsuffix}" \
			-I$fault_dir/development/include/src \
			-I$prefix/include \
			-I$prefix/include/python$pyversion$pyabi \
			"-DMODULE_QNAME=$targetname" \
			"-DMODULE_PACKAGE=$pkgname" \
			"-DMODULE_BASENAME=$modname" \
			"-DFACTOR_BASENAME=$modname" \
			"-DF_PURPOSE=debug" \
			-fwrapv \
			src/*.c || exit

		cd "$fault_dir/$project"
	done

	cd "$original"
done
