set -e

apt update
# Install dependencies.
[[ -d /dependencies ]] && dpkg -i /dependencies/*.deb || \
  apt -f install -y --no-install-recommends

# Make read-write copy of source code.
mkdir -p /build
cp -a /source-ro /build/source
cd /build/source

# If a source tarball exists, copy it to the build directory.
[ -d /tarball ] && cp /tarball/* /build

# Install build dependencies.
mk-build-deps -ir \
  -t 'apt-get -o Debug::pkgProblemResolver=yes -y --no-install-recommends' \
  debian/control

# Build packages.
debuild -b -uc -us

# Copy packages to output dir with user's permissions.
cp -a /build/*.deb /output/
chown -R $USER:$GROUP /output
