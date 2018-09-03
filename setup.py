from setuptools import setup, find_packages

setup(
    name='owca',
    author='Intel',
    description='Orchestration-aware Workload Collocation Agent',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Distributed Computing',
    ],
    install_requires=[
          'requests==2.19.1',
          'ruamel.yaml==0.15.37',
          'colorlog==3.1.4',
          'logging-tree==1.7',
          'dataclasses==0.6',
          'confluent-kafka==0.11.4'
    ],
    tests_require=[
          'pytest',
          'pytest-cov',
          'flake8'
    ],
    packages=find_packages(),
    python_requires=">=3.6",
    use_scm_version=True,
    setup_requires=[
        'setuptools_scm'
    ],

)
