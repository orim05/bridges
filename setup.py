from setuptools import find_packages, setup

setup(
    name="bridges",
    version="0.2.0",
    description="A framework-agnostic middleware for automatic UI generation.",
    author="orim05",
    author_email="orimeiri18@email.com",
    license="MIT",
    url="https://github.com/orim05/bridges",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "pydantic",
        "rich",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
