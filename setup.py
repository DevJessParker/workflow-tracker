from setuptools import setup, find_packages

setup(
    name="workflow-tracker",
    version="0.1.0",
    description="A tool to scan repositories and extract data workflow diagrams",
    author="Your Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "workflow-tracker=cli.main:cli",
        ],
    },
    python_requires=">=3.9",
)
