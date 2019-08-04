class MethodData(object):
    def __init__(self, method_name, start_line, end_line, contents, changed_indices, method_used_lines, parameters, file_name):
        self.method_name = method_name
        self.start_line = int(start_line)
        self.end_line = int(end_line)
        self.implementation = contents[self.start_line - 1: self.end_line]
        self.method_used_lines = method_used_lines
        self.changed = self._is_changed(changed_indices)
        self.parameters = parameters
        self.file_name = file_name
        self.id = self.file_name + "@" + self.method_name + "(" + ",".join(self.parameters) + ")"

    def _is_changed(self, changed_indices):
        # return len(set(self.method_used_lines).intersection(set(indices))) > 0
        return any(filter(lambda ind: ind in self.method_used_lines, changed_indices))
        # return any(filter(lambda ind: ind >= self.start_line and ind <= self.end_line, indices))

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.method_name == other.method_name and self.parameters == other.parameters

    def __repr__(self):
        return self.id