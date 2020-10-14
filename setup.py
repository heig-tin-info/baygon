import setuptools
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

name='heigtest'

def get_property(prop, project):
    result = re.search(r'__{}__\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/__init__.py').read())
    return result.group(1)

setuptools.setup(
    name=name,
    version=get_property('version', name),
    author=get_property('author', name),
    author_email=get_property('email', name),
    description=get_property('description', name),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/heig-tin-info/heig-test",
    install_requires=["voluptuous", "click", "pyaml", "colorama"],
    packages=setuptools.find_packages(),
    license="MIT",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={"console_scripts": ["info-test=heigtest.__main__:cli"]},
)
