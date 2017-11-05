#!/usr/bin/env python36

from termcolor import colored
from pathlib import Path

import contextlib, docker, io, os, plac, sys, tarfile


IMAGE_DIST_LABEL = 'ddb-image-dist'
IMAGE_VER_LABEL = 'ddb-version'
DDB_VER = '0'

ROOT = Path(__file__).parent.absolute()


def note(s): return colored(s, 'cyan')
def error(s): return colored(s, 'red')


def get_script(script): return str(ROOT / 'scripts' / script)


class BuildContext:
    def __init__(self, dist, outdir, srcdir, depdir):
        self.dist = dist
        self.outdir = outdir
        self.srcdir = srcdir
        self.depdir = depdir

        self.client = docker.from_env()

    def get_image(self):
        for image in self.client.images.list():
            if (image.labels.get(IMAGE_DIST_LABEL) == self.dist and
                image.labels.get(IMAGE_VER_LABEL) == DDB_VER):
                return image

        return None

    def build_image(self):
        dockerfile = f'''
        FROM {self.dist}
        COPY setup.sh /setup.sh
        RUN bash /setup.sh
        '''

        tario = io.BytesIO()
        with tarfile.open(fileobj=tario, mode='w') as tf:
            tf.add(get_script('setup.sh'), 'setup.sh')

            dockerfile_info = tarfile.TarInfo('Dockerfile')
            dockerfile_info.size = len(dockerfile)
            tf.addfile(tarinfo=dockerfile_info,
                       fileobj=io.BytesIO(dockerfile.encode('utf-8')))

        tario.seek(0)

        output = self.client.api.build(tag=f'ddb-image-{self.dist}', quiet=False,
                                       fileobj=tario, rm=True, custom_context=True,
                                       decode=True, labels={IMAGE_DIST_LABEL: self.dist,
                                                            IMAGE_VER_LABEL: DDB_VER})

        for line in output:
            if 'error' in line:
                print(error(line['error']))
                sys.exit(1)
            elif 'aux' in line:
                return self.client.images.get(line['aux']['ID'])
            elif 'status' in line:
                continue
            else:
                assert 'stream' in line, line
                print(line['stream'], end='')

        assert False

    @contextlib.contextmanager
    def temporary_container(self, image, command, volumes, environment):
        container = self.client.containers.run(image, command, detach=True, remove=True,
                                               volumes=volumes, tty=True,
                                               environment=environment)

        try:
            yield container
        finally:
            try:
                container.remove(force=True)
            except docker.errors.APIError as ex:
                if ('Conflict' not in ex.response.reason and
                    'Not Found' not in ex.response.reason):
                    raise

    def run(self, image):
        print(note('Creating temporary container...'))

        volumes = {
            str(self.srcdir.absolute()): {
                'bind': '/source-ro',
                'mode': 'ro',
            },
            str(self.outdir.absolute()): {
                'bind': '/output',
                'mode': 'rw',
            },
            get_script('run.sh'): {
                'bind': '/run.sh',
                'mode': 'ro',
            },
        }

        if self.depdir is not None:
            volumes[str(self.depdir.absolute())] = {
                'bind': '/dependencies',
                'mode': 'ro',
            }

        environment = {
            'USER': str(os.getuid()),
            'GROUP': str(os.getgid()),
        }

        with self.temporary_container(image, 'bash /run.sh', volumes,
                                      environment) as container:
            stream = container.logs(stdout=True, stderr=True, stream=True)
            for item in stream:
                print(item, end='')

            container.wait()


class DDB:
    commands = 'build', 'clean'

    def build(self, dist: 'The distribution to use', outdir: 'The output directory',
              depdir: ('The deb dependency directory', 'option'),
              srcdir: ('The source directory') = '.',
              arch: ('The build architecture', 'option', None, str,
                     ['x86', 'x64']) = 'x64',
              force: ('Rebuild the image, even if not necessary', 'flag') = False):
        '''
        Builds a deb package using the given architecture and Ubuntu/Debian distribution.
        '''
        if not dist.startswith('ubuntu:') or dist.startswith('debian:'):
            print(error('distribution should be ubuntu:version or debian:version'))
            sys.exit(1)

        srcdir = Path(srcdir)
        outdir = Path(outdir)
        if depdir is not None:
            depdir = Path(depdir)

        if arch == 'x86':
            dist = f'i386/{dist}'

        if not (srcdir / 'debian' / 'control').exists():
            print(error('The source directory should contain a debian/control file'))
            sys.exit(1)

        client = docker.from_env()

        ctx = BuildContext(dist, outdir, srcdir, depdir)

        image = None
        if not force:
            print(note('Checking for prebuilt image...'))
            image = ctx.get_image()
        if image is None:
            if force:
                print(note('-force was passed; building image...'))
            else:
                print(note('No image found: building one...'))
            image = ctx.build_image()

        ctx.run(image)

    def clean(self):
        '''Removes old images created by ddb.'''
        client = docker.from_env()

        print(note('Cleaning up old images...'))

        cleaned = False

        for image in client.images.list():
            if image.labels.get(IMAGE_VER_LABEL, DDB_VER) != DDB_VER:
                print(note(f'Removing old image {image.id}...'))
                client.images.remove(image.id)
                cleaned = True

        if cleaned:
            print(note('Success!'))
        else:
            print(note('No images to clean were found.'))


def main():
    try:
        plac.call(DDB())
    except SystemExit as ex:
        # XXX: hack
        if ex.code is None and '-h' not in sys.argv and '--help' not in sys.argv:
            sys.exit('A command is required!')


if __name__ == '__main__':
    main()
