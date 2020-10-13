#!/usr/bin/env python
import pkutils

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = list(pkutils.parse_requirements('requirements.txt'))
dependencies = list(pkutils.parse_requirements('requirements.txt', True))
dev_requirements = list(pkutils.parse_requirements('dev-requirements.txt'))
readme = pkutils.read('README.rst')
module = pkutils.parse_module('heig-test/__init__.py')
version = module.__version__
project = module.__title__
email = module.__email__
user = pkutils.get_user(email)

setup(
    name=project,
    version=version,
    description=module.__description__,
    long_description=readme,
    author=module.__author__,
    author_email=email,
    install_requires=requirements,
    tests_require=dev_requirements,
    dependency_links=dependencies,
    setup_requires=['pkutils'],
    url=pkutils.get_url(project, user),
    download_url=pkutils.get_dl_url(project, user, version),
    classifiers=[
        pkutils.get_license(module.__license__),
        pkutils.get_status(version),
        ...
    ],
    packages=['heig-test']
)
