import difflib
import gc

from SourceFile import SourceFile


class FileDiff(object):
    REMOVED = '- '
    ADDED = '+ '
    UNCHANGED = '  '
    NOT_IN_INPUT = '? '
    BEFORE_PREFIXES = [REMOVED, UNCHANGED]
    AFTER_PREFIXES = [ADDED, UNCHANGED]

    def __init__(self, diff, commit_sha):
        self.file_name = diff.b_path
        self.commit_sha = commit_sha
        self.is_ok = self.file_name.endswith(".java")
        if not self.is_ok:
            return
        before_contents = ['']
        after_contents = ['']
        if diff.new_file:
            assert diff.a_blob is None
        else:
            try:
                before_contents = diff.a_blob.data_stream.stream.readlines()
            except:
                gc.collect()
        if diff.deleted_file:
            assert diff.b_blob is None
        else:
            try:
                after_contents = diff.b_blob.data_stream.stream.readlines()
            except:
                gc.collect()
        before_indices, after_indices = self.get_changed_indices(before_contents, after_contents)
        self.before_file = SourceFile(before_contents, diff.a_path, before_indices)
        self.after_file = SourceFile(after_contents, diff.b_path, after_indices)

    def is_java_file(self):
        return self.is_ok

    @staticmethod
    def get_changed_indices(before_contents, after_contents):
        def get_lines_by_prefixes(lines, prefixes):
            return filter(lambda x: any(map(lambda p: x.startswith(p), prefixes)), lines)

        def get_indices_by_prefix(lines, prefix):
            return map(lambda x: x[0], filter(lambda x: x[1].startswith(prefix), enumerate(lines)))

        diff = list(difflib.ndiff(before_contents, after_contents))

        diff_before_lines = get_lines_by_prefixes(diff, FileDiff.BEFORE_PREFIXES)
        assert map(lambda x: x[2:], diff_before_lines) == before_contents
        before_indices = get_indices_by_prefix(diff_before_lines, FileDiff.REMOVED)

        diff_after_lines = get_lines_by_prefixes(diff, FileDiff.AFTER_PREFIXES)
        assert map(lambda x: x[2:], diff_after_lines) == after_contents
        after_indices = get_indices_by_prefix(diff_after_lines, FileDiff.ADDED)

        return before_indices, after_indices

    def get_changed_methods(self):
        return filter(lambda method: method.changed,
                      self.before_file.methods.values() + self.after_file.methods.values())

    def __repr__(self):
        return self.file_name