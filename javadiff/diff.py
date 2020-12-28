try:
    import StringIO
except:
    from io import StringIO
import gc
import json
import sys

import git
import jira

try:
    from .CommitsDiff import CommitsDiff
    from .FileDiff import FileDiff
except:
    from CommitsDiff import CommitsDiff
    from FileDiff import FileDiff

from functools import reduce


def get_commit_diff(git_path, child, parent=None, analyze_source_lines=True):
    repo = git.Repo(git_path)
    if isinstance(child, str):
        child = repo.commit(child)
    if not parent:
        parent = child.parents[0]
    return CommitsDiff(child, parent, analyze_source_lines=analyze_source_lines)


def get_commit_methods(git_path, child, parent=None, analyze_source_lines=True):
    repo = git.Repo(git_path)
    if isinstance(child, str):
        child = repo.commit(child)
    if not parent:
        parent = child.parents[0]
    file_diffs =  CommitsDiff(child, parent, analyze_source_lines=analyze_source_lines).diffs
    methods = []
    for file_diff in file_diffs:
        gc.collect()
        if file_diff.is_java_file():
            methods.extend(file_diff.get_methods())
    return methods


def get_changed_exists_methods(git_path, child, parent=None, analyze_source_lines=True):
    repo = git.Repo(git_path)
    if isinstance(child, str):
        child = repo.commit(child)
    if not parent:
        parent = child.parents[0]
    return get_changed_exists_methods_from_file_diffs(CommitsDiff(child, parent, analyze_source_lines=analyze_source_lines).diffs)


def get_modified_functions(git_path):
    repo = git.Repo(git_path)
    diffs = repo.head.commit.tree.diff(None, None, True, ignore_blank_lines=True, ignore_space_at_eol=True)
    return get_changed_methods_from_file_diffs(map(lambda d: FileDiff(d, repo.head.commit.hexsha, git_dir=git_path), diffs))


def get_changed_methods_from_file_diffs(file_diffs):
    methods = []
    for file_diff in file_diffs:
        gc.collect()
        if file_diff.is_java_file():
            methods.extend(file_diff.get_changed_methods())
    return methods


def get_changed_exists_methods_from_file_diffs(file_diffs):
    methods = []
    for file_diff in file_diffs:
        gc.collect()
        if file_diff.is_java_file():
            methods.extend(file_diff.get_changed_exists_methods())
    return methods


def get_java_commits(git_path):
    repo = git.Repo(git_path)
    data = repo.git.log('--pretty=format:"sha: %H"', '--name-only').split("sha: ")
    comms = dict(map(lambda d: (d[0], filter(lambda x: x.endswith(".java"), d[1:-1])),
                     map(lambda d: d.replace('"', '').replace('\n\n', '\n').split('\n'), data)))
    return dict(map(lambda x: (repo.commit(x), comms[x]), filter(lambda x: comms[x], comms)))


def get_methods_descriptions(git_path, json_out_file):
    repo = git.Repo(git_path)
    repo_files = filter(lambda x: x.endswith(".java") and not x.lower().endswith("test.java"),
                        repo.git.ls_files().split())
    commits = []
    for commit, files in get_java_commits(git_path).items():
        if any(filter(lambda f: f in files, repo_files)):
            commits.append(commit)
    methods_descriptions = {}
    print("# commits to check: {0}".format(len(commits)))
    for i in range(len(commits[:30]) - 1):
        print("inspect commit {0} of {1}".format(i, len(commits)))
        methods = get_changed_methods(git_path, commits[i], analyze_source_lines=False)
        if methods:
            map(lambda method: methods_descriptions.setdefault(method, StringIO.StringIO()).write(
                commits[i].message), methods)
    with open(json_out_file, "wb") as f:
        data = dict(map(lambda x: (x[0].method_name_parameters, x[1].getvalue()), methods_descriptions.items()))
        json.dump(data, f)


def get_methods_per_commit(git_path, json_out_file):
    repo = git.Repo(git_path)
    commits = list(repo.iter_commits())
    methods_per_commit = {}
    for i in range(len(commits) - 1):
        try:
            methods = get_changed_methods(git_path, commits[i + 1], analyze_source_lines=False)
        except:
            continue
        if methods:
            methods_per_commit[commits[i].hexsha] = map(repr, methods)
    with open(json_out_file, "wb") as f:
        json.dump(methods_per_commit, f)
