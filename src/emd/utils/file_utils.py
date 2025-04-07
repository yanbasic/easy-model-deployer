import os

def mkdir_with_mode(directory,exist_ok=True,mode=0o777):
    oldmask = os.umask(0)
    os.makedirs(directory, mode=mode,exist_ok=exist_ok)
    os.umask(oldmask)
