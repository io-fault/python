#!/bin/sh
# Bootstrapping for fault.
# Creates the C modules that are needed to build

fault="$1"; shift 1
python="$(which "$1")"; shift 1
pyversion="$("$python" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
pyabi="$("$python" -c 'import sys; print(sys.abiflags)')"

prefix="$(dirname "$(dirname "$python")")"
test $? -eq 0 || exit 1

compile ()
{
	echo "$@"
	compiler="$1"; shift 1

	"$compiler" "$@"
}

case "$(uname -s)" in
	*Darwin*)
		osflags="-Xlinker -bundle -Xlinker -undefined -Xlinker dynamic_lookup";
	;;
	*)
		osflags="-Xlinker -shared -Xlinker --export-all-symbols -Xlinker --export-dynamic"
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
		cd "$module"
		modname="$(basename "$(pwd)")"

		fullname="$(module_path "$(pwd)")"
		targetname="$(echo "$fullname" | sed 's/.extensions//')"
		pkgname="$(echo "$fullname" | sed 's/[.][^.]*$//')"

		compile ${CC:-cc} -o "../../${modname}.so" \
			$osflags \
			-Xlinker -L$prefix/lib \
			-Xlinker -lc -Xlinker -lpython$pyversion$pyabi \
			-I$fault_dir/development/include \
			-I$prefix/include \
			-I$prefix/include/python$pyversion$pyabi \
			-include $fault_dir/development/include/fault.h \
			-include $fault_dir/development/include/cpython.h \
			-include $fault_dir/development/include/xpython.h \
			"-DMODULE_QNAME=$targetname" \
			"-DMODULE_PACKAGE=$pkgname" \
			"-DMODULE_BASENAME=$modname" \
			"-DF_ROLE_ID=F_DEBUG_ROLE_ID" \
			-fPIC -fwrapv -g \
			src/*.c || exit

		cd "$fault_dir/$project"
	done

	cd "$original"
done
