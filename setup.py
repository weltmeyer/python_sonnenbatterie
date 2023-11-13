import pathlib
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="sonnenbatterie", # Replace with your own username
    version="0.2.7",
    author="Jan Weltmeyer",
    author_email="author@example.com",
    description="Access Sonnenbatterie REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/weltmeyer/python_sonnenbatterie",
    packages=["sonnenbatterie"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires='>=3.6',
    install_requires=["requests"],
)