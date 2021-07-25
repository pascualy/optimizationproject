from setuptools import setup, find_packages


setup(
    name="final_project",
    version="1.0",
    packages=find_packages(),
    install_requires=['gurobipy', 'pytest', 'tabulate']
)