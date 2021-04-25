from .lib.module import Module
from .lib.thread import Thread
from .lib.context import global_context


class IgnoredEventsUpdater(Thread):
    def __init__(self, sender_module):
        super().__init__()
        self.mod = sender_module

    def do_run(self):
        resp = global_context.cec_api.fetch("/v1/journal/ignored")
        self.mod.ignored = set(resp)

class CecJournalSender(Thread):
    def __init__(self, entry):
        super().__init__()
        self.entry = entry

    def do_run(self):
        global_context.cec_api.submit("/v1/journal/send", self.entry.as_dict())

class PlatformSender(Module):
    def __init__(self):
        self.ignored = None

    def on_start(self, plugin_dir):
        IgnoredEventsUpdater(self).start()

    def on_journal_entry(self, entry):
        if self.ignored is None:
            return
        if entry.event in self.ignored:
            return
        job = CecJournalSender(entry)
        job.start()
