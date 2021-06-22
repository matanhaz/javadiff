from diff import get_commit_diff

if __name__ == "__main__":
    c = r"98628d9724cb29ea25583c756e61052ceff45cf6"
    m = get_commit_diff(r"C:\Temp\camel2", c)
    m.get_metrics()

    pass


