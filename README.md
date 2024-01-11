# Bayesian Capstone Project 2023

To reproduce the development environment using conda, download conda for your operating system:

```bash
$ yes | conda create --name capstone_env python=3.10
$ conda activate capstone_env
$ pip3 install pipenv
```

Install dependencies with:

```bash
$ pipenv install
```

Activate the virtual environment (the virtual environment will be created within the conda environment the first time):

```bash
$ pipenv shell
```

To install dependencies:

```bash
$ pipenv install package_name
# Or, to install packages in other package categories
$ pipenv install package_name --categories category_name
```