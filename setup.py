from setuptools import setup, find_packages
from pathlib import Path
import re

cd = Path(__file__).parent
tuple_regex = re.compile(r'\((.*)\)')
name = 'sqlite_file_index'


def get_version_components():
    init_path = cd/name/'__init__.py'
    with open(init_path) as init_file:
        for line in init_file:
            if line.startswith('version_components'):
                for match in tuple_regex.finditer(line):
                    return map(int, match.group(1).split(','))


def get_version():
    return '.'.join(
        map(str, get_version_components())
    )


def get_long_description():
    with open("README.md", "r") as file:
        return file.read()


setup(
    name='sqlite-file-index',
    version=get_version(),
    packages=find_packages(),
    url='https://github.com/0xf0f/sqlite-file-index',
    license='MIT',
    author='0xf0f',
    author_email='',
    description='Hierarchical file index in an sqlite database.',
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
