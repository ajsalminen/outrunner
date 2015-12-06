from setuptools import setup
import sys


setup(name='outrunner',
      version='0.1',
      description='Watch directories and run tasks when the contents change.',
      url='http://github.com/ajsalminen/outrunner',
      author='Antti Salminen',
      author_email='mail-projects.outrunner@facingworlds.com',
      license='MIT',
      entry_points={
          'console_scripts': [
              'outrunner = outrunner:main'
          ],
      },
      package_data={'outrunner': ['outrunner.conf.yml', 'outrunner.plugin.zsh']},
      packages=['outrunner'],
      zip_safe=False,
      include_package_data=False)
