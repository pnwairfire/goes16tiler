from setuptools import setup, find_packages

from goes16tiler import __version__

requirements = []
with open('requirements.txt') as f:
    requirements = [r for r in f.read().splitlines() if not r.startswith('-')]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='goes16tiler',
    version=__version__,
    license='GPLv3+',
    author='Stuart Illson',
    author_email='stuartillson@gmail.com',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    scripts=[
    ],
    classifiers=[
        "Development Status :: 2 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        'Natural Language :: English',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ],
    package_data={

    },
    url='https://github.com/pnwairfire/goes16tiler',
    description='Generates tiled basemaps from GOES-16 data for web mapping applications',
    install_requires=requirements
)
