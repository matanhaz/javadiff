from diff import get_java_commits, get_changed_methods, get_changed_methods_from_file_diffs
import sys
import os
import shutil
import git
import gc
from projects import projects
from tempfile import mkdtemp
try:
    from .CommitsDiff import FormatPatchCommitsDiff
except:
    from CommitsDiff import FormatPatchCommitsDiff


def topic_modeling_data(project_ind):
    git_link, jira_link = projects[sorted(projects.keys())[int(project_ind)]]
    jira_project_name = os.path.basename(jira_link)
    git_path = os.path.abspath(r"repo")
    out_dir = os.path.abspath(r"out_dir")
    os.system("git clone {0} repo".format(git_link))
    os.mkdir(out_dir)
    os.mkdir(os.path.join(out_dir, jira_project_name))
    path_to_format_patch = mkdtemp()
    repo = git.Repo(git_path)
    commits_diffs = dict()
    for f in repo.git.format_patch("--root", "-o", path_to_format_patch, "--function-context", "--unified=900000", "--full-index", "--patch", "-k", "--numbered-files", "--no-stat", "-N").split():
        cd = FormatPatchCommitsDiff(os.path.normpath(os.path.join(path_to_format_patch, f)), analyze_source_lines=False)
        commits_diffs[cd.commit] = cd
    # repo_files = list(filter(lambda x: x.endswith(".java") and not x.lower().endswith("test.java"),
    #                     repo.git.ls_files().split()))
    #
    # for commit in list(repo.iter_commits())[:30]:
        # if any(filter(lambda f: f in files, repo_files)):
        #     commits.append(commit)
    methods_descriptions = {}
    methods_per_commit = {}
    for commit in list(repo.iter_commits())[:30]:
        methods = get_changed_methods_from_file_diffs(commits_diffs[commit.hexsha].diffs)
        if methods:
            map(lambda method: methods_descriptions.setdefault(method, StringIO.StringIO()).write(
                commit.message), methods)
            methods_per_commit[commit.hexsha] = list(map(repr, methods))
    with open(os.path.join(out_dir, jira_project_name, "methods_descriptions.json"), "wb") as f:
        data = dict(map(lambda x: (x[0].method_name_parameters, x[1].getvalue()), methods_descriptions.items()))
        json.dump(data, f)
    with open(os.path.join(out_dir, jira_project_name, "methods_per_commit.json"), "wb") as f:
        json.dump(methods_per_commit, f)

    issues = get_jira_issues(jira_project_name, r"http://issues.apache.org/jira")
    issues = dict(map(lambda issue: (issue, issues[issue][1]), filter(lambda issue: issues[issue][0] == 'bug', issues)))
    with open(os.path.join(out_dir, jira_project_name, "bugs_data.json"), "wb") as f:
        json.dump(commits_and_issues(gitPath, issues), f)

    shutil.rmtree(path_to_format_patch)
    shutil.make_archive(project_ind, 'zip', out_dir)


if __name__ == "__main__":
    topic_modeling_data(sys.argv[1])
