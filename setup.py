from setuptools import setup, find_packages

exec(open("NBA_data_scraper/_version.py").read())

setup(
    name="NBA_data_scraper",
    version=__version__,
    description="Module for scraping NBA data using selenium.",
    author="Willy Liu",
    author_email="willyliu802@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pandas>=0.25.1",
        "pyyaml>=5.3.1",
        "selenium>=3.141.0",
        "numpy>=1.19.4",
    ],
    python_requires=">=3.6",
)