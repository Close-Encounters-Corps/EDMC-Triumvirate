from .lib.module import Module
from .lib.thread import Thread
from .lib.context import global_context


class CecJournalSender(Thread):
    def __init__(self, entry):
        super().__init__()
        self.entry = entry

    def do_run(self):
        global_context.cec_api.submit("/v1/journal", self.entry.as_dict())

class PlatformSender(Module):
    def on_journal_entry(self, entry):
        job = CecJournalSender(entry)
        job.start()
