
from subprocess import run as srun
from os import path as ospath
from sys import executable
from os import execl as osexecl

UPSTREAM_REPO = 'https://github.com/Aluval/StreamCleanX'
UPSTREAM_BRANCH = 'SH24BOTS'

if UPSTREAM_REPO is not None:
    if ospath.exists('.git'):
        srun(["rm", "-rf", ".git"])

    update = srun([f"git init -q \
                     && git config --global user.email sunriseseditsoffical249@gmail.com \
                     && git config --global user.name metamorpher \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)


    if update.returncode == 0:
        osexecl(executable, executable, "bot.py")
    else:
        print('Something went wrong while updating, check UPSTREAM_REPO if valid or not!')

osexecl(executable, executable, "bot.py")
