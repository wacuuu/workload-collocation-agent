from typing import Dict, List


class PerfCounters:
    def __init__(self, cgroup_path: str, events: List[str]):
        self.cgroup_path = cgroup_path
        self.events = events

        # DO the magic and enabled everything + start counting
        self._metrics = {event: 0 for event in events}

    def read_metrics(self) -> Dict[str, int]:
        return self._metrics

    def cleanup(self):
        pass

    def get_metrics(self):
        return {}
