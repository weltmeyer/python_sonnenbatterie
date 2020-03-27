
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sonnenbatterie", # Replace with your own username
    version="0.0.1",
    author="Jan Weltmeyer",
    author_email="author@example.com",
    description="Access Sonnenbatterie REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GNU General Public License v3.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)