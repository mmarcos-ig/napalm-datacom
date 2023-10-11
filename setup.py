"""setup.py file."""

import uuid

from setuptools import setup, find_packages

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name="napalm-datacom",
    version="0.1.0",
    packages=find_packages(),
    author="IGN",
    author_email="qbinterface@ignetworks.com",
    description="Network Automation and Programmability Abstraction Layer with Multivendor support",
    classifiers=[
        'Topic :: Utilities',
         'Programming Language :: Python',
         'Programming Language :: Python :: 2',
         'Programming Language :: Python :: 2.7',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    url="https://github.com/mmarcos-ig/ign-napalm-datacom",
    include_package_data=True,
    install_requires=reqs,
)
