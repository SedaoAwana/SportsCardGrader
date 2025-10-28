from setuptools import setup, find_packages

setup(
    name="sports-card-grader",
    version="1.0.0",
    description="Analyze sports cards to predict grading scores",
    author="Sports Card Grader Team",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
        "pillow>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sports-card-grader=sports_card_grader.cli:main",
        ],
    },
    python_requires=">=3.7",
)