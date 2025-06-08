from git_filter_repo import Filter
import sys

class RemoveAuthorFilter(Filter):
    def filter_commit(self, commit):
        if commit.author_email == "mailtomrsrinivasulu@gmail.com":
            return None
        return commit

if __name__ == "__main__":
    filter = RemoveAuthorFilter()
    filter.run()from git_filter_repo import Filter
    import sys
    
    class RemoveAuthorFilter(Filter):
        def filter_commit(self, commit):
            if commit.author_email == "mailtomrsrinivasulu@gmail.com":
                return None
            return commit
    
    if __name__ == "__main__":
        filter = RemoveAuthorFilter()
        filter.run()