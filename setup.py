#!/usr/bin/env python

from setuptools import find_packages, setup

def main():
    return setup(
        name='verif',
        version="0.1",
        description="model verification package",
        url="git@github.com:MetServiceDev/verif-data.git",
        packages=find_packages(include="*"),
        include_package_data=True,
        package_data={"": ["data/*.yaml", "data/*.json"]},
        install_requires=["s3fs",
                          "boto3",
                          "numpy",
                          "pandas",
                          "pyarrow",
                          "PyYAML",
                          "scipy",
                          "xarray",
                          "matplotlib",
                          "h5netcdf",
                          "dask",
                          "flox",
                        #   "dt-output",
                          "properscoring"]
    )

if __name__ == "__main__":
    main()
