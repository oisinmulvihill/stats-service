# -*- coding: utf-8 -*-
"""
Setuptools script for stats_service (stats_service)

"""
from setuptools import setup, find_packages

Name = 'stats_service'
ProjectUrl = ""
Version = "1.0.0"
Author = 'Oisin Mulvihill'
AuthorEmail = 'oisin mulvihill at gmail'
Maintainer = Author
Summary = (
    'Analytics Gathering REST API Endpoint for storing metrics in InfluxDB.'
)
License = 'MIT License'
Description = Summary
ShortDescription = Summary

needed = [
    # 'evasion-common',
    'pyyaml',
    'ua-parser',
    'user-agents',
    'pycountry',
    'requests',
    'newrelic',
    'influxdb',
    'apiaccesstoken',
    'Pyramid',
    'waitress',
    'stats-client',
]

test_needed = [
    'pytest',
]

test_suite = ''

EagerResources = [
    'stats',
]
ProjectScripts = [
]

PackageData = {
    '': ['*.*'],
}

EntryPoints = """
[paste.app_factory]
main = stats_service.service:main
"""

import sys
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    url=ProjectUrl,
    name=Name,
    cmdclass={'test': PyTest},
    zip_safe=False,
    version=Version,
    author=Author,
    author_email=AuthorEmail,
    description=ShortDescription,
    long_description=Description,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    keywords='web wsgi bfg pylons pyramid',
    license=License,
    scripts=ProjectScripts,
    install_requires=needed,
    tests_require=test_needed,
    test_suite=test_suite,
    include_package_data=True,
    packages=find_packages(),
    package_data=PackageData,
    eager_resources=EagerResources,
    entry_points=EntryPoints,
)
