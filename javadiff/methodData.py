import operator
import javalang
from collections import Counter

class SourceLine(object):
    def __init__(self, line, line_number, is_changed, ordinal, decls, tokens):
        self.line = line.strip()
        self.line_number = line_number
        self.is_changed = is_changed
        self.ordinal = ordinal
        self.decls = decls
        self.tokens = tokens

    def __repr__(self):
        start = "  "
        if self.is_changed:
            start = "* "
        return "{0}{1}: {2}".format(start, str(self.line_number), self.line)

    @staticmethod
    def get_source_lines(start_line, end_line, contents, changed_indices, method_used_lines, parsed_body, tokens=None):
        source_lines = []
        used_lines = []
        for line_number in range(start_line - 1, end_line):
            if line_number not in method_used_lines:
                continue
            used_lines.append(line_number)
        decls = SourceLine.get_decls_by_lines(parsed_body, list(map(lambda x: x + 1, used_lines)))
        tokens_types = SourceLine.get_tokens_by_lines(tokens, list(map(lambda x: x + 1, used_lines)))
        for line_number in used_lines:
            line = contents[line_number]
            is_changed = line_number in changed_indices
            source_lines.append(SourceLine(line, line_number, is_changed, line_number-start_line, decls[line_number + 1], tokens_types[line_number + 1]))
        return source_lines

    @staticmethod
    def get_decls_by_lines(parsed_body, lines):
        def helper(x):
            return x.position and x.position.line in lines
        def getter(x):
            return x[1]
        ans = {}
        for l in lines:
            ans[l] = []
        for e in parsed_body:
            for e2 in map(getter, e.filter(object)):
                e3 = list(filter(helper, map(getter, e2.filter(javalang.ast.Node))))
                for x in e3:
                    ans[x.position.line].append(e2)
        res = {}
        for l in ans:
            res[l] = dict(Counter(map(lambda x: type(x).__name__, ans[l])))
        return res

    @staticmethod
    def get_tokens_by_lines(tokens, lines):
        def get_name(t):
            if type(t).__name__ not in ['Identifier', 'DecimalInteger']:
                # return type(t).__name__
                return "{0}_{1}".format(type(t).__name__, t.value)
            else:
                # return "{0}_{1}".format(type(t).__name__, t.value)
                return type(t).__name__
        ans = {}
        for l in lines:
            ans[l] = []
        for t in tokens:
            if t.position.line in lines:
                    ans[t.position.line].append(get_name(t))
        res = {}
        for l in ans:
            res[l] = dict(Counter(ans[l]))
        return res


class MethodData(object):
    def __init__(self, method_name, start_line, end_line, contents, changed_indices, method_used_lines, parameters, file_name, method_decl, analyze_source_lines=True, tokens=None):
        self.method_name = method_name
        self.start_line = int(start_line)
        self.end_line = int(end_line)
        self.implementation = contents[self.start_line - 1: self.end_line]
        self.method_used_lines = method_used_lines
        self.parameters = parameters
        self.file_name = file_name
        self.method_decl = method_decl
        self.return_type = None
        if hasattr(self.method_decl, 'return_type'):
            self.return_type = getattr(self.method_decl, 'return_type')
        self.method_name_parameters = self.method_name + "(" + ",".join(self.parameters) + ")"
        self.id = self.file_name + "@" + self.method_name_parameters
        self.source_lines = None
        self.changed = self._is_changed(changed_indices)
        if analyze_source_lines:
            self.source_lines = SourceLine.get_source_lines(start_line, end_line, contents, changed_indices, method_used_lines, method_decl.body, tokens)

    def _is_changed(self, indices=None):
        if self.source_lines:
            return any(filter(lambda line: line.is_changed, self.source_lines))
        # return any(filter(lambda ind: ind >= self.start_line and ind <= self.end_line, indices))
        return len(set(self.method_used_lines).intersection(set(indices))) > 0

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.method_name == other.method_name and self.parameters == other.parameters

    def __repr__(self):
        return self.id

    def get_changed_lines(self):
        return filter(lambda line: line.is_changed, self.source_lines)