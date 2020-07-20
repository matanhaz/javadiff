from diff import get_methods_descriptions, get_methods_per_commit, get_bugs_data
import sys
import os
import shutill
from projects import projects


def topic_modeling_data(project_ind):
    git_link, jira_link = projects[sorted(projects.keys())[int(project_ind)]]
    jira_project_name = os.path.basename(jira_link)
    os.system("git clone {0} repo".format(git_link))
    gitPath = os.path.abspath(r"repo")
    out_dir = os.path.abspath(r"out_dir")
    os.mkdir(out_dir)
    os.mkdir(os.path.join(out_dir, jira_project_name))
    get_methods_descriptions(gitPath, os.path.join(out_dir, jira_project_name, "methods_descriptions.json"))
    get_methods_per_commit(gitPath, os.path.join(out_dir, jira_project_name, "methods_per_commit.json"))
    get_bugs_data(gitPath, jira_project_name, os.path.join(out_dir, jira_project_name, "bugs_data.json"))
    shutil.make_archive(project_ind, 'zip', out_dir)


if __name__ == "__main__":
    project_ind = sys.argv[1]
    topic_modeling_data(project_ind)
