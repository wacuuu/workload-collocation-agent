=============
wca-scheduler
=============

.. contents:: Table of Contents

**This software is pre-production and should not be deployed to production servers.**

Introduction
============
wca-scheduler is special type of controller that assigns pods to nodes using provided algorithms. 

Configuration
=============
You can configure scheduler in following way in ``config.yaml``:  

.. code-block:: yaml

        loggers:
          scheduler.main: DEBUG
        algorithm: !NOPAlgorithm
          ...

Algorithms
==========
To implement your algorithm you need only to use inferace below:

.. code-block:: python

        #  https://github.com/kubernetes/kubernetes/blob/release-1.15/pkg/scheduler/api/types.go#L299
        @dataclass
        class ExtenderFilterResult():
            Nodes: List[Dict] = None
            NodeNames: List[str] = field(default_factory=lambda: [])
            FailedNodes: Dict[str, str] = field(default_factory=lambda: {})
            Error: str = ''


        #  https://github.com/kubernetes/kubernetes/blob/release-1.15/pkg/scheduler/api/types.go#L331
        @dataclass
        class HostPriority():
            Host: str
            Score: int

            def __repr__(self):
                return '%s=%s' % (self.Host, self.Score)


        #  https://github.com/kubernetes/kubernetes/blob/release-1.15/pkg/scheduler/api/types.go#L284
        @dataclass
        class ExtenderArgs:
            Nodes: List[Dict]
            Pod: Dict[str, str]
            NodeNames: List[str]

        class Algorithm(ABC):

            @abstractmethod
            def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
                pass

            @abstractmethod
            def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
                pass

Example deployment
==================
Check documentation of `example deployment <../examples/kubernetes/wca-scheduler/README.rst>`_
