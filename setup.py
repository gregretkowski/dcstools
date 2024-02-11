from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

long_description = ''
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    for line in f:
        if line.startswith('## Sample'):
            break
        long_description += line

setup(
    name="dcstools",
    version='0.0.1',
    description="Scripts I use for editing missions",
    long_description=long_description,
    url='https://github.com/gregretkowski/dcstools',
    author="Greg Retkowski",
    author_email="greg@rage.net",
    license="LGPLv3",
    classifiers=[
    ],
    keywords='dcs digital combat simulator eagle dynamics',
    install_requires=[
    ],
    packages=[
    ],
    package_data={
    },
    entry_points={
    },
    test_suite="tests"
)
