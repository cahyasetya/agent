from setuptools import find_packages, setup
import os

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read README.md for long description
long_description = ""
# Check if README.md exists before attempting to read it
if os.path.isfile("README.md"):
    with open("README.md", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="ai-agent",
    version="0.2.0",  # Match version in __init__.py
    packages=find_packages(include=['agent', 'agent.*']),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "agent = agent.main:main",
        ],
    },
    author="Your Name",
    author_email="your@email.com",
    description="A file system agent with AI assistance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yourrepository",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
