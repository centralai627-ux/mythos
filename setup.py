from setuptools import setup, find_packages

setup(
    name="mythos-ai",
    version="1.0.0",
    description="Mythos AI - Autonomous Agent with CLI and Desktop Interface",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Mythos AI Team",
    url="https://github.com/centralai627-ux/mythos",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        "prompt_toolkit>=3.0.0",
        "fpdf2>=2.7.0",
        "pypdf>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mythos=mythos:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
