from pathlib import Path

from setuptools import find_namespace_packages, setup


with open("hydra_plugins/hydra_orion_sweeper/__init__.py") as file:
    for line in file.readlines():
        if 'version' in line:
            version = line.split('=')[1].strip().replace('"', "")
            break

setup(
    name="hydra-orion-sweeper",
    version=version,
    author="Pierre Delaunay",
    author_email="pierre.delaunay@mila.quebec",
    description="Hydra Orion Sweeper plugin",
    long_description=(Path(__file__).parent / "README.rst").read_text(),
    url="https://orion.readthedocs.io/",
    packages=find_namespace_packages(include=["hydra_plugins.*"]),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
    setup_requires=[
        'setuptools',
    ],
    install_requires=[
        'typing_extensions',
        "hydra-core>=1.2",
        "orion>=0.2.2",
    ],
    include_package_data=True,
)
