import pathlib

from setuptools import find_packages, setup

import tom_rhymer

_THIS_DIR = pathlib.Path(__file__).parent


def _get_requirements():
    with (_THIS_DIR / 'requirements.txt').open() as fp:
        return fp.read()


setup(
    name='tom_rhymer',
    version=tom_rhymer.__version__,
    install_requires=_get_requirements(),
    package_dir={'tom_rhymer': 'tom_rhymer'},
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    package_data={
        'tom_rhymer': ['data/rhymer.pkl'],
    },
)
