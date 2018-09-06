from setuptools import setup, find_packages

setup(
    name='owca_kafka_consumer',
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
