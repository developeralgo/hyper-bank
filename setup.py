from setuptools import setup, find_packages

setup(
    name="hyper",
    version="0.0.1",
    description="Medical utilities: PubMed search, calculator index, and more.",
    long_description=open("README.md").read() if __import__('os').path.exists('README.md') else '',
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/hyper",  # Update with your repo if available
    packages=find_packages(),
    install_requires=[
        "requests",
        "lxml",
        "beautifulsoup4",
        "pymongo",
    ],
    python_requires=">=3.7",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
