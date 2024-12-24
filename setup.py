import pathlib
import re

from setuptools import find_packages, setup

_PACKAGE_NAME = "tom_rhymer"
_THIS_DIR = pathlib.Path(__file__).parent


def _get_version():
    init_file = _THIS_DIR / _PACKAGE_NAME / "__init__.py"
    with init_file.open("r") as f:
        content = f.read()

    version_pattern = re.compile(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', flags=re.MULTILINE
    )
    version_match = version_pattern.search(content)

    if not version_match:
        raise RuntimeError("Unable to find version string")

    return version_match.group(1)


def _get_requirements():
    with (_THIS_DIR / "requirements.txt").open() as fp:
        reqs = fp.read().splitlines()
        return [r for r in reqs if r and not r.startswith("#")]


setup(
    name=_PACKAGE_NAME,
    version=_get_version(),
    install_requires=_get_requirements(),
    package_dir={_PACKAGE_NAME: _PACKAGE_NAME},
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"tom_rhymer": ["data/rhymer.pkl"]},
    include_package_data=True,
)
