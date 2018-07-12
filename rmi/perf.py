from typing import List


class PerfCounters:
    def __init__(self, cgroup_path: str, events: List[str]):
        self.cgroup_path = cgroup_path
        self.events = events

        # DO the magic and enabled everything + start counting
        self._metrics = {event: 0 for event in events}

    def cleanup(self):
        # TODO: implement me
        return

    def get_metrics(self):
        return self._metrics
