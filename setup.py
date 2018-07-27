from setuptools import setup, find_packages

setup(
    name='rmi_kafka_consumer',
    version='0.0.1',
    author='Intel',
    description='Expose data from kafka to prometheus',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Distributed Computing',
    ],
    install_requires=[
          'confluent-kafka==0.11.4'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
          'pytest',
          'pytest-cov',
          'flake8'
    ],
    packages=find_packages(),
    python_requires=">=3.6",
)
