#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = []

test_requirements = []

setup(
    author="Tristan Bereau",
    author_email="tristan.bereau@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description=(
        "Python Boilerplate contains all the boilerplate "
        "you need to create a Python package."
    ),
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="my_scientific_profile",
    name="my_scientific_profile",
    packages=find_packages(
        include=["my_scientific_profile", "my_scientific_profile.*"]
    ),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/tbereau/my_scientific_profile",
    version="0.1.0",
    zip_safe=False,
)
