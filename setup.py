"""
TSB Door Service Assistant
A Streamlit application for diagnosing and troubleshooting TSB doors.
"""

from setuptools import setup, find_packages

# Read requirements
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="object-error-handling-service",
    version="1.0.0",
    author="Respeak",
    author_email="tim.rietz@respeak.io",
    description="Service Assistant Application",
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={"console_scripts": ["tsb-door-service=service.app:main"]},
    package_data={"tsb_door_service": ["data/*.json"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Customer Service",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
