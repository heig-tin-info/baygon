import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="heigtest",
    version="0.1.0",
    author="Yves Chevallier",
    author_email="yves.chevallier@heig-vd.ch",
    description="Functional tests for teaching activity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/heig-tin-info/heig-test",
    install_requires=["voluptuous", "click", "pyaml"],
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
)
