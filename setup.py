from setuptools import setup, find_packages
# Use this for installing the package using pip for usage in shell

setup(
    name="fontGadgets",
    version="0.1.101",
    description="A package to add more functions to fontParts and defcon objects.",
    author="Bahman Eslami",
    author_email="contact@bahman.design",
    url="http://bahman.design",
    license="MIT",
    platforms=["Any"],
    package_dir={'': 'fontgadgets.roboFontExt/lib'},
    packages=find_packages('fontgadgets.roboFontExt/lib'),
    install_requires=[
    "fontParts",
    "fontTools",
    "ufo2ft",
    "ufoLib2",
    "pytest",
    "ufonormalizer"
    ],
    tests_require=[
        'pytest>=3.7',
    ],
)
