# Building Tensorflow 1.10.0 with MKL support
FROM centos:7 AS tensorflow

# Tensorflow build dependencies
RUN yum install -y wget git which
RUN yum groupinstall -y 'Development Tools'
RUN yum install -y epel-release
RUN yum install -y python36 python36-devel
# Install pip3.6
RUN python3.6 -m ensurepip --default-pip
RUN pip3.6 install \
    six \
    numpy \
    wheel
# Repository for bazel tool installation
RUN wget https://copr.fedorainfracloud.org/coprs/vbatts/bazel/repo/epel-7/vbatts-bazel-epel-7.repo\
    -P /etc/yum.repos.d/
RUN yum install -y bazel

# Env variables that configure tensorflow build
ENV CI_BUILD_PYTHON python3.6
ENV TF_NEED_CUDA 0
ENV TF_NEED_MKL 1

# Build tensorflow .whl package
RUN git clone https://github.com/tensorflow/tensorflow
RUN cd /tensorflow && \
    git checkout tags/v1.10.0 && \
    tensorflow/tools/ci_build/builds/configured CPU && \
    bazel build --config=mkl --config=opt //tensorflow/tools/pip_package:build_pip_package && \
    bazel-bin/tensorflow/tools/pip_package/build_pip_package /output

# Building final container with workload
FROM centos:7

# Tensorflow and workload runtime dependencies
RUN yum install -y epel-release
RUN yum install -y python36
# Install pip3.6
RUN python3.6 -m ensurepip --default-pip
COPY --from=tensorflow /output /tensorflow-pkg
RUN pip3.6 install \
    wheel \
    h5py \
    pillow \
    /tensorflow-pkg/*.whl
# Cleanup wheel and tensorflow package after install
RUN pip3.6 uninstall -y wheel
RUN rm -rf /tensorflow-pkg
# Add and run resnet50 weights loading script
ADD tensorflow-inference/load_nn_weights.py /load_nn_weights.py
RUN python3.6 load_nn_weights.py
# Add workload dataset and workload script
ADD tensorflow-inference/fruits-360 /fruits-360
ADD tensorflow-inference/inference.py /inference.py
# Create symlink for workload runner and inferencescript
RUN ln -s /inference.py /usr/local/bin/inference
# Make workload launcher and training scripts executables
RUN chmod +x /inference.py
ADD /wrapper/dist/wrapper.pex /wrapper.pex

