
from FileDiff import FileDiff


class CommitsDiff(object):
    def __init__(self, child, parent, analyze_source_lines=True):
        self.diffs = list(CommitsDiff.diffs(child, parent, analyze_source_lines=analyze_source_lines))

    @staticmethod
    def diffs(child, parent, analyze_source_lines=True):
        for d in parent.tree.diff(child.tree, ignore_blank_lines=True, ignore_space_at_eol=True):
            try:
                yield FileDiff(d, child.hexsha, analyze_source_lines=True)
            except Exception as e:
                pass
