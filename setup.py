from setuptools import setup, find_packages

setup(
    name="bridges",
    version="0.1.1",
    description="A framework-agnostic middleware for automatic UI generation.",
    author="orim05",
    author_email="orimeiri18@email.com",
    license="MIT",
    url="https://github.com/orim05/bridges",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
