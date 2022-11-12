import re

import setuptools

with open("discord_oauth/__init__.py") as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("version is not set")

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess

        p = subprocess.Popen(
            ['git', 'rev-list', '--count', 'HEAD'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

setuptools.setup(
    name="discord-fastapi-oauth",
    author="Riksou",
    url="https://github.com/Riksou/discord-fastapi-oauth",
    version=version,
    packages=setuptools.find_packages(),
    install_requires=requirements,
    python_requires=">=3.8"
)
