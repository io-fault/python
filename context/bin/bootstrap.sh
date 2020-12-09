#!/bin/sh
# Usage: sh fault/context/bootstrap.sh <fault-dir-path> <python3>
# Bootstrapping for fault Python product.
# Creates the C modules that are needed to build factors.

fault="$1"; shift 1
if ! test -d "$fault"
then
	echo >&2 "first parameter must be the 'fault' (python) context package root directory."
	exit 1
fi

sysint="$1"; shift 1
if ! test -d "$sysint"
then
	echo >&2 "second parameter must be the 'system' (integration) context package root directory."
	exit 1
fi

python="$(which "$1")"; shift 1
if ! test -x "$python"
then
	echo >&2 "third parameter must be the Python implementation to build for."
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

pyversion="$("$python" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
pyabi="$("$python" -c 'import sys; print(sys.abiflags)')"
pytype="$("$python" -c 'import sys; print(sys.implementation.name)')"

test $? -eq 0 || exit 1

echo "ABI: $pyabi"
echo "VERSION: $pyversion"
echo "TYPE: $pytype"

compile ()
{
	compiler="$1"; shift 1
	echo
	echo ">>>"
	echo "$compiler" $osflags "$@"
	echo "<<<"
	echo

	"$compiler" $osflags "$@"
}

defsys=`uname -s | tr "[:upper:]" "[:lower:]"`
defarch=`uname -m | tr "[:upper:]" "[:lower:]"`

platsuffix="so" # Following platform switch overrides when necessary.

case "$defsys" in
	*darwin*)
		osflags="-Wl,-bundle,-undefined,dynamic_lookup,-lSystem,-L$prefix/lib,-lpython$pyversion$pyabi -fPIC";
	;;
	*freebsd*)
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

# Inside fault/; Only fault.system has extensions.
for project in ./system
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
		iscache="$(echo "$module" | grep '__pycache__\|__f-cache__\|__f-int__')"
		if ! test x"$iscache" = x""
		then
			continue
		fi

		cd "$module"
		pwd
		modname="$(basename "$(pwd)")"

		fullname="$(module_path "$(pwd)")"
		package="$(cd ..; module_path "$(pwd)")"
		projectfactor="$(cd ../..; module_path "$(pwd)")"
		targetname="$(echo "$fullname" | sed 's/.extensions//')"
		pkgname="$(echo "$fullname" | sed 's/[.][^.]*$//')"

		compile ${CC:-cc} -v -o "../../${modname}.${platsuffix}" \
			-I$sysint/python/include/src \
			-I$sysint/machine/include/src \
			-I$fault_dir/system/include/src \
			-I$prefix/include \
			-I$prefix/include/python$pyversion$pyabi \
			"-DF_SYSTEM=$defsys" \
			"-DF_TARGET_ARCHITECTURE=$defarch" \
			"-DF_INTENTION=debug" \
			"-DF_FACTOR_DOMAIN=system" \
			"-DF_FACTOR_TYPE=extension" \
			"-DFACTOR_BASENAME=$modname" \
			"-DFACTOR_SUBPATH=$modname" \
			"-DFACTOR_PROJECT=$projectfactor" \
			"-DFACTOR_PACKAGE=$package" \
			"-DFACTOR_QNAME=$fullname" \
			-fwrapv \
			src/*.c

		cd "$fault_dir/$project"
	done

	cd "$original"
done
