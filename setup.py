#!/usr/bin/env python


from setuptools import find_packages, setup

def main():
    return setup(
        name='verif',
        version="0.1",
        description="model verification package",
        url="git@github.com:MetServiceDev/verif-data.git",
        packages=find_packages(include="*"),
        install_requires=["s3fs",
                          "boto3",
                          "numpy",
                          "pandas",
                          "scipy",
                          "xarray",
                          "matplotlib",
                          "h5netcdf",
                          "dask",
                          "dt-output",
                          "properscoring"]
    )

if __name__ == "__main__":
    main()
