from setuptools import setup, find_packages

with open("README.md", "r") as file:
    long_description = file.read()

setup(
    name='sqlite-file-index',
    version='1.4',
    packages=find_packages(),
    url='https://github.com/0xf0f/sqlite-file-index',
    license='MIT',
    author='0xf0f',
    author_email='',
    description='Hierarchical file index in an sqlite database.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
