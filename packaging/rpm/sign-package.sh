#!/bin/sh

set -eu

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 RUTA_AL_RPM" >&2
    exit 2
fi

package=$1
key_file="$(dirname "$0")/../keys/RPM-GPG-KEY-Pep-Simo.asc"

if [ ! -f "$package" ]; then
    echo "No existe el RPM: $package" >&2
    exit 1
fi

if [ ! -f "$key_file" ]; then
    echo "No existe la clave pública: $key_file" >&2
    exit 1
fi

package_dir=$(dirname -- "$package")
package_name=$(basename -- "$package")

rpmsign --addsign "$package"
rpm -Kv "$package"

(
    cd "$package_dir"
    sha256sum "$package_name" > "$package_name.sha256"
    sha256sum -c "$package_name.sha256"
)

install -m 644 "$key_file" "$package_dir/RPM-GPG-KEY-Pep-Simo.asc"
