from setuptools import find_packages, setup

setup(
    name="ai-agent",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["agent"],
    install_requires=[
        "requests",
        "prompt_toolkit",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "agent = agent:__main__",
        ],
    },
    author="Your Name",
    author_email="your@email.com",
    description="A file system agent with AI assistance",
    long_description=open("README.md").read() if "README.md" else "",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yourrepository",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
