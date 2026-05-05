from setuptools import setup, find_packages

setup(
    name="phpoptimizer",
    version="0.1.0",
    description="Analyseur et optimiseur de code PHP",
    author="Votre Nom",
    author_email="votre.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.0.0",
        "colorama>=0.4.0",
        "phply>=1.2.6",
        "pathlib>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "phpoptimizer=phpoptimizer.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
