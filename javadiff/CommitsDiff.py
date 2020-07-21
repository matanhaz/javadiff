from difflib import restore
try:
    from .FileDiff import FileDiff, FormatPatchFileDiff
except:
    from FileDiff import FileDiff, FormatPatchFileDiff


class CommitsDiff(object):
    def __init__(self, child, parent, analyze_source_lines=True):
        self.diffs = list(CommitsDiff.diffs(child, parent, analyze_source_lines=analyze_source_lines))

    @staticmethod
    def diffs(child, parent, analyze_source_lines=True):
        for d in parent.tree.diff(child.tree, ignore_blank_lines=True, ignore_space_at_eol=True):
            try:
                yield FileDiff(d, child.hexsha, analyze_source_lines=analyze_source_lines)
            except Exception as e:
                pass


class FormatPatchDiff(object):
    DEV_NULL = '/dev/null'

    def __init__(self, lines):
        self.a_path = lines[0][6:].replace('\n', '')
        self.b_path = lines[1][6:].replace('\n', '')
        self.normal_diff = map(lambda x: x[0] + " " + x[1:], lines[2:])
        self.new_file = self.a_path == Diff.DEV_NULL
        self.deleted_file = self.b_path == Diff.DEV_NULL
        self.before_contents = ['']
        if not self.new_file:
            self.before_contents = list(restore(self.normal_diff, 1))
        self.after_contents = ['']
        if not self.deleted_file:
            self.after_contents = list(restore(self.normal_diff, 1))


class FormatPatchCommitsDiff(object):
    def __init__(self, file_name, analyze_source_lines=True):
        self.diffs = FormatPatchCommitsDiff.diffs(file_name, analyze_source_lines=analyze_source_lines)

    @staticmethod
    def diffs(file_name, analyze_source_lines):
        with open(file_name) as f:
            lines = f.readlines()[:-3]
        if len(lines) == 0:
            pass
        commit_sha = str(lines[0].split()[1])  # line 0 word 1
        diff_inds = map(lambda x: x[0], filter(lambda x: x[1].startswith("diff --git"), enumerate(lines))) + [len(lines)]
        diffs = map(lambda diff: FormatPatchDiff(lines[diff[0] + 2: diff[1]]), zip(diff_inds, diff_inds[1:]))
        for d in diffs:
            try:
                yield FormatPatchFileDiff(d, commit_sha, analyze_source_lines=analyze_source_lines)
            except:
                pass


