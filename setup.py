#!/usr/bin/env python3
import os

import setuptools


def read(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)

    with open(filepath) as fobj:
        return fobj.read()


setuptools.setup(
    name="kieli",
    version="1.0.1",
    author="PurpleMyst",
    description="Minimalistic language server protocol client.",
    long_description=read("README.rst"),
    license="MIT",
    url="https://github.com/PurpleMyst/kieli",
    py_modules=["kieli"],
    install_requires=["attrs"],
)
