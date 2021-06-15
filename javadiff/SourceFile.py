import operator
import javalang
import os
import sys
import lizard
import tempfile
import traceback
from functools import reduce
try:
    from .commented_code_detector import CommentFilter
    from .methodData import MethodData, SourceLine
    from .commented_code_detector import Halstead
except:
    from methodData import MethodData, SourceLine
    from commented_code_detector import CommentFilter
    from commented_code_detector import Halstead


class SourceFile(object):
    def __init__(self, contents, file_name, indices=(), analyze_source_lines=True, delete_source=True):
        self.contents = contents
        self.changed_indices = indices
        self.file_name = file_name
        self.lizard_analysis = None
        self.methods = dict()
        self.path_to_source = None
        try:
            f, self.path_to_source = tempfile.mkstemp()
            os.close(f)
            if sys.version_info.major == 3:
                with open(self.path_to_source, 'w', encoding="utf-8") as f:
                    f.writelines(contents)
            else:
                with open(self.path_to_source, 'wb') as f:
                    f.writelines(contents.encode("UTF-8"))
            self.lizard_analysis = lizard.analyze_file(self.path_to_source)
            self.lizard_values = {}
            for att in ['CCN', 'ND', 'average_cyclomatic_complexity', 'average_nloc', 'average_token_count', 'nloc', 'token_count']:
                try:
                    setattr(self, 'lizard_' + att, getattr(self.lizard_analysis, att))
                    self.lizard_values[att] = getattr(self.lizard_analysis, att)
                except:
                    setattr(self, 'lizard_' + att, None)
                    self.lizard_values[att] = 0
            if delete_source:
                self.remove_source()
            tokens = list(javalang.tokenizer.tokenize("".join(self.contents)))
            parser = javalang.parser.Parser(tokens)
            parsed_data = parser.parse()
            packages = list(map(operator.itemgetter(1), parsed_data.filter(javalang.tree.PackageDeclaration)))
            classes = list(map(operator.itemgetter(1), parsed_data.filter(javalang.tree.ClassDeclaration)))
            self.package_name = ''
            if packages:
                self.package_name = packages[0].name
            else:
                pass
            self.modified_names = list(map(lambda c: self.package_name + "." + c.name, classes))
            self.methods, self.used_lines = self.get_methods_by_javalang(tokens, parsed_data, analyze_source_lines=analyze_source_lines)
            self.used_changed_lines = set(self.changed_indices).intersection(self.used_lines)
            if analyze_source_lines:
                self.decls = SourceLine.get_decles_empty_dict()
                for k in self.decls:
                    self.decls[k] = sum(list(map(lambda m: self.methods[m].decls[k], self.methods)))
                self.halstead = Halstead(reduce(list.__add__, list(map(lambda m: list(map(lambda s: s.halstead_line, m.source_lines)), self.methods.values())), [])).getValuesVector()
        except Exception as e:
            traceback.print_exc()
            raise

    def remove_source(self):
        os.remove(self.path_to_source)

    def get_methods_by_javalang(self, tokens, parsed_data, analyze_source_lines=True):
        def get_method_end_position(method, seperators):
            method_seperators = seperators[list(map(id, sorted(seperators + [method],
                                                          key=lambda x: (x.position.line, x.position.column)))).index(
                id(method)):]
            assert method_seperators[0].value == "{"
            counter = 1
            for seperator in method_seperators[1:]:
                if seperator.value == "{":
                    counter += 1
                elif seperator.value == "}":
                    counter -= 1
                if counter == 0:
                    return seperator.position

        halstead_lines = CommentFilter().filterComments(self.contents)[0]
        used_lines = set(map(lambda t: t.position.line-1, tokens))
        seperators = list(filter(lambda token: isinstance(token, javalang.tokenizer.Separator) and token.value in "{}",
                            tokens))
        methods_dict = dict()
        for class_declaration in map(operator.itemgetter(1), parsed_data.filter(javalang.tree.ClassDeclaration)):
            class_name = class_declaration.name
            methods = list(map(operator.itemgetter(1), class_declaration.filter(javalang.tree.MethodDeclaration)))
            constructors = list(map(operator.itemgetter(1), class_declaration.filter(javalang.tree.ConstructorDeclaration)))
            for method in methods + constructors:
                if not method.body:
                    # skip abstract methods
                    continue
                method_start_position = method.position
                method_end_position = get_method_end_position(method, seperators)
                method_used_lines = list(filter(lambda line: method_start_position.line <= line <= method_end_position.line, used_lines))
                parameters = list(map(lambda parameter: parameter.type.name + ('[]' if parameter.type.children[1] else ''), method.parameters))
                lizard_method = list(filter(lambda f: f.start_line == method_start_position.line, self.lizard_analysis.function_list))
                if lizard_method:
                    lizard_method = lizard_method[0]
                else:
                    lizard_method = None
                method_data = MethodData(".".join([self.package_name, class_name, method.name]),
                                         method_start_position.line, method_end_position.line,
                                         self.contents, halstead_lines, self.changed_indices, method_used_lines, parameters, self.file_name, method, tokens, analyze_source_lines=analyze_source_lines, lizard_method=lizard_method)
                methods_dict[method_data.id] = method_data
        return methods_dict, used_lines

    def get_changed_methods(self):
        return list(filter(lambda method: method.changed, self.methods.values()))

    def replace_method(self, method_data):
        assert method_data.method_name in self.methods
        old_method = self.methods[method_data.method_name]
        self.contents = self.contents[:old_method.start_line] + \
                        self.contents[method_data.start_line:method_data.end_line] + \
                        self.contents[old_method.end_line:]
        self.methods = self.get_methods_by_javalang()

    @staticmethod
    def get_hunks_count(indices):
        if len(indices) == 0:
            return 0
        elif len(indices) == 1:
            return 1
        hunks = 1
        s = sorted(indices)
        for i,j in zip(s, s[1:]):
            if i + 1 != j:
                hunks += 1
        return hunks

    def __repr__(self):
        return self.file_name

    def get_file_metrics(self):
        d = {'changed_lines': len(self.changed_indices), 'used_lines': len(self.used_lines), 'changed_used_lines': len(self.used_changed_lines),
              'methods_count': len(self.methods), 'lines_hunks': self.get_hunks_count(self.changed_indices), 'used_lines_hunks': self.get_hunks_count(self.used_changed_lines)}
        for k in self.lizard_values:
            d[k] = self.lizard_values[k]
        for k in self.decls:
            d[k] = self.decls[k]
        for k in self.halstead:
            d[k] = self.halstead[k]
        return d
