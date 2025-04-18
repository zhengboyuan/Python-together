from setuptools import setup, find_packages

setup(
    name="charging_station",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        line.strip() for line in open("requirements.txt") if line.strip()
    ],
    include_package_data=True,
    python_requires=">=3.10",
)
