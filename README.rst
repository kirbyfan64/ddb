ddb
===

ddb is a lightweight tool that lets you easily use Docker containers to build .deb packages
for Debian or Ubuntu.

The scripts used for building were largely based on
`docker-deb-builder <https://github.com/tsaarni/docker-deb-builder>`_.

Usage
*****

Say we have a package we want to build. Run::

  $ cd source-directory
  $ ddb build ubuntu:xenial xenial-debs

This will create a new x64 Xenial build image, build the deb package inside, and output
it to *xenail-debs*.

The first argument is the Linux distribution to use. You can use any of the tags
`here <https://store.docker.com/images/ubuntu>`_ or
`here <https://store.docker.com/images/debian>`_. For instance, you could build on
Debian Jessie via::

  $ ddb build debian:jessie xenial-debs

You can also build x86 packages, too::

  $ ddb build ubuntu:xenial xenial-debs -a x86

If you need to install dependencies to build your package that aren't available in the
default apt repositories, you can do::

  $ ddb build ubuntu:xenial xenial-debs -d my-depdir

Here, ``-d`` points to a directory with deb packages. Before building your package, ddb
will install all the deb files in the ``my-depdir`` directory.

You can also build from a different directory by passing it as the third argument::

  $ ddb build ubuntu:xenial xenial-debs my-source-directory
