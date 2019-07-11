from itertools import imap

from FileDiff import FileDiff


class CommitsDiff(object):
    def __init__(self, commit_a, commit_b, repo_files):
        self.diffs = imap(lambda d: FileDiff(d, commit_b.hexsha, repo_files), commit_a.tree.diff(commit_b.tree))