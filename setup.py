from setuptools import setup

setup(name='uncore_regulator',
      version='0.1',
      description='',
      author='Etienne ANDRE',
      author_email='etienne.andre@telecom-sudparis.eu',
      packages=['uncore_regulator'],
      install_requires=[
          'pylikwid',
      ],
      scripts=[
          'bin/uncore-regulator'
      ],
      zip_safe=False)
