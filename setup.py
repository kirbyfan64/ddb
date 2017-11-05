from setuptools import setup


with open('README.rst') as fp:
    readme = fp.read()

with open('requirements.txt') as fp:
    requirements = fp.read().splitlines()


setup(
    name='ddb',
    version='0.1',
    description='A lightweight tool for building .deb packages via Docker containers',
    long_description=readme,
    author='Ryan Gonzalez',
    author_email='rymg19@gmail.com',
    license='MIT',
    url='https://github.com/kirbyfan64/ddb',
    py_modules=['ddb'],
    entry_points={
        'console_scripts': ['ddb = ddb:main']
    },
    install_requires=requirements,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Archiving :: Packaging',
    ],
)
