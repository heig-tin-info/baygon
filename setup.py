import setuptools
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

name = 'baygon'


def get_property(prop, project):
    result = re.search(r'__{}__\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop),
                       open(project + '/__init__.py').read())
    return result.group(1)


setuptools.setup(
    author_email=get_property('email', name),
    author=get_property('author', name),
    description=get_property('description', name),
    install_requires=["voluptuous", "click", "pyaml", "colorama"],
    test_requirements=['flake8', 'tox'],
    extras_require={
        'dev': ['flake8', 'tox']
    },
    license="MIT",
    long_description_content_type="text/markdown",
    long_description=long_description,
    name=name,
    packages=setuptools.find_packages(),
    url="https://github.com/heig-tin-info/baygon",
    version=get_property('version', name),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: Education",
        "Operating System :: OS Independent",
    ],
    keywords=["testing", "functional-testing", ],
    python_requires='>=3.6',
    py_modules=[name],
    entry_points={"console_scripts": [f"{name}={name}.__main__:cli"]},
)
