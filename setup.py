from setuptools import setup, find_packages

# jupyter labextension install ipysheet
setup(
    name="final_project",
    version="1.0",
    packages=find_packages(),
    install_requires=['gurobipy', 'pytest', 'tabulate']
)