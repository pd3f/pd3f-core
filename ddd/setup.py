from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

classifiers = [
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "License :: OSI Approved :: BSD License",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

setup(
    name="ddd",
    version="0.0.0",
    python_requires=">=3.7",
    description="DDD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jfilter/ptf-ddd",
    author="Johannes Filter",
    author_email="hi@jfilter.de",
    license="GPL",
    packages=find_packages(),
    zip_safe=True,
    classifiers=classifiers,
    install_requires=["parsr-client==3.1", "clean-text", "unidecode", "joblib", "dehyphen"],
)
