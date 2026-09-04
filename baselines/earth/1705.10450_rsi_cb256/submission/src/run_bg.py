"""Run a python script as a detached daemon: python3 src/run_bg.py logfile <script> [args...]

The caller returns immediately; output goes to logfile. Double-fork + setsid so
the grandchild survives the calling shell/tool session and holds no inherited
stdout/stderr pipe.
"""
import os
import sys


def main():
    argv = sys.argv[1:]
    if not argv:
        print("usage: run_bg.py <logfile> <script> [args...]")
        return 1
    logpath = argv[0]
    script = argv[1]
    rest = argv[2:]
    pid = os.fork()
    if pid > 0:
        return 0
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    fd = os.open(logpath, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.execvp(sys.executable, [sys.executable, "-u", script, *rest])


if __name__ == "__main__":
    sys.exit(main())