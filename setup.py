import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spotifyAPI-rafacarrasco",
    version="0.0.1",
    author="Rafael Carrasco",
    author_email="rafacarrasco07@gmail.com",
    description="A SpotifyAPI Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/erdos2n/spotifyAPI",
    packages=setuptools.find_packages(),
    license="GPL",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)