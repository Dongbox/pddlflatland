from setuptools import setup, find_packages

setup(name='pddlflatland',
      version='0.0.1',
      install_requires=['matplotlib', 'pillow', 'gym', 'imageio'],
      packages=find_packages(),
      include_package_data=True,
)

