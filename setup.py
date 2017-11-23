# -*- coding: utf-8 -*-
__author__ = 'xtwxfxk'


from setuptools import setup, Command, find_packages
import io
import re
import os

curdir = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(curdir, "README.md")).read()

def version():
    ret = re.findall(r'VERSION: (.*)', README)[0]
    return ret.strip()


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()

packages = find_packages()

def get_data_files():
    sep = os.path.sep
    # install the datasets
    data_files = {}

    for r, ds, fs in os.walk(os.path.join(curdir, "lutils/ext")):
        r_ = os.path.relpath(r, start=curdir)
        data_files.update({r_.replace(sep, ".") : ["*.xpi", ]})

    return data_files

package_data = get_data_files()
package_data.update({"lutils" : ["header", "logging.conf", "ser", "user_agent", "user_agent_all"]})



setup(
    name="lutils",
    version=version(),
    author="xtwxfxk",
    author_email="xtwxfxk@163.com",
    description="",
    long_description=README,
    license="BSD",
    keywords="lutils",
    url="https://github.com/xtwxfxk/lutils",
    packages=packages,
    package_data = package_data,
    platforms=['any'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",

        "Programming Language :: Python :: Implementation :: CPython",
        "Natural Language :: English",

        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
    ],
    include_package_data=False,
    install_requires=read_requirements('requirements.txt')
)