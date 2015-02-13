""" Import Fabric module dependencies
"""
from fabric.api import cd, local, settings, env, prefix, run, task
from fabric.contrib.files import exists
from fabric.operations import _prefix_commands, _prefix_env_vars
import posixpath
import re

#
# Some static parameters
DEPLOY_ROOT = '/usr/share'
CODE_BRANCH = 'master'
PROJECT_NAME = 'northants'
REPO_NAME = 'coursolve_need203'
VIRTUALENV = 'northants'
VIRTUALENVS_DIR = '/usr/share/virt_env'

env.hosts = ['root@stockwatch.ws']
env.code_repo = 'git@github.com:coursolve-northamptonshire/coursolve_need203.git'

# Now the environment parameters, generated from the statics
env.code_dir = '/'.join([DEPLOY_ROOT, PROJECT_NAME])
env.project_dir = '/'.join([DEPLOY_ROOT, PROJECT_NAME, REPO_NAME])
env.static_root = '/'.join([DEPLOY_ROOT, PROJECT_NAME, 'static'])
env.virtualenv = '/'.join([VIRTUALENVS_DIR, VIRTUALENV])

#env.django_settings_module = 'climateexchange.settings'

env.project_name = PROJECT_NAME
env.project_user = "www-data"
env.project_group = "www-data"
env.project_user_password = "northants1234"
env.project_db_name = "northants_db"
env.project_db_user = "root"
env.project_db_password = "northants1234"

# Python version
PYTHON_BIN = "python2.7"
PYTHON_PREFIX = ""  # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = "%s/bin/%s" % (PYTHON_PREFIX, PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN

# Set to true if you can restart your webserver (via wsgi.py), false to stop/start your webserver
# CHANGEME
#DJANGO_SERVER_RESTART = False

# Python version
PYTHON_BIN = "python2.7"
PYTHON_PREFIX = ""  # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = "%s/bin/%s" % (PYTHON_PREFIX, PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN


def virtualenv(venv_dir):
    """
    Context manager that establishes a virtualenv to use.
    """
    return settings(venv=venv_dir)


def run_venv(command, **kwargs):
    """
    Runs a command in a virtualenv (which has been specified using
    the virtualenv context manager
    """
    run("source %s/bin/activate" % env.virtualenv + " && " + command, **kwargs)

def ensure_virtualenv():
    """ Ensure the virtualernv exists on the server 
    """
    if not exists(env.virtualenv):
        with cd(env.code_dir):
            run("sudo virtualenv --no-site-packages --python=%s %s" %
                (PYTHON_BIN, env.virtualenv), )    
    run("sudo echo %s > %s/lib/%s/site-packages/projectsource.pth" %
        (env.project_dir, env.virtualenv, PYTHON_BIN))
    run("sudo chown -Rf %s:%s %s" % (env.project_user, env.project_group, env.virtualenv))

def ensure_src_dir():
    """ Ensure the source code directory exists on the server
    """
    if not exists(env.code_dir):
        run("sudo mkdir -p %s" % env.code_dir)
    run("sudo chown -Rf %s:%s %s" % (env.project_user, env.project_group, env.code_dir))
    
def ensure_src():
    """ Make sure the source is checked out on the server
    """
    ensure_src_dir()
    with cd(env.code_dir):
        if not exists(posixpath.join(env.code_dir, '.git')):
            run("sudo git clone %s ." % (env.code_repo))
        if not exists('/'.join([env.code_dir, 'db'])):
            run("sudo mkdir -p %s" % '/'.join([env.code_dir, 'db']))
        if not exists('/'.join([env.code_dir, 'media'])):
            run("sudo mkdir -p %s" % '/'.join([env.code_dir, 'media']))
        if not exists('/'.join([env.code_dir, 'static'])):
            run("sudo mkdir -p %s" % '/'.join([env.code_dir, 'static']))
        if not exists('/'.join([env.code_dir, 'logs'])):
            run("sudo mkdir -p %s" % '/'.join([env.code_dir, 'logs']))
        run("sudo chown -Rf %s:%s %s" % (env.project_user, env.project_group, env.code_dir))

def push_sources():
    """ Push source code to server
    """
    ensure_src()
    local(' '.join(['git checkout', CODE_BRANCH]))
    local(' '.join(['git push origin', CODE_BRANCH]))
    with cd(env.code_dir):
        #run(' '.join(['sudo git checkout', CODE_BRANCH]))
        run(' '.join(['sudo git pull origin', CODE_BRANCH]))
        run(' '.join(['sudo git checkout', CODE_BRANCH]))
        #run('sudo cp -f climateexchange/settings/deploy.py climateexchange/settings/local.py')
        run("sudo chown -Rf %s:%s %s" % (env.project_user, env.project_group, env.code_dir))

def fetch_stop():
    """ Stop data fetching
    """
    pass

def install_dependencies():
    """ Install the python dependencies we need
    """
    ensure_virtualenv()
    with virtualenv(env.virtualenv):
        with cd(env.code_dir):
            run_venv("easy_install -U distribute")
            run_venv("pip install -r tools/requirements.txt")
            run("sudo chown -Rf %s:%s %s" % (env.project_user, env.project_group, env.virtualenv))

def ssh_keygen():
    """ Generates a pair of DSA keys in root's .ssh directory.
    """
    ensure_virtualenv()
    with virtualenv(env.virtualenv):
        with cd(env.code_dir):
            if not exists("~/.ssh/id_dsa.pub"):
                run("mkdir -p %s" % "~/.ssh/")
                run("sudo mkdir -p %s" % "/root/.ssh/")
                run("sudo ssh-keygen -q -t dsa -f '%s' -N ''" % '/root/.ssh/id_dsa')
                #run("sudo cp -f /root/.ssh/id_dsa ~/.ssh/")
                #run("sudo cp -f /root/.ssh/id_dsa.pub ~/.ssh/")
                #run("sudo chown -Rf %s:%s ~/.ssh/" % (env.project_user, env.project_group))

def packages():
    """ Generator to read in package names to install 
    """    
    re_comment = re.compile(r"^\#.*$", re.I)
    with open("tools/packages.txt", "r") as packages_file:
        for line in packages_file:
            if re_comment.match(line):
                continue
            package_name = line.strip()
            yield package_name


@task 
def provision():
    """
    Provisions the target with package rdependencies
    """
    run("sudo apt-get update")
    # TO DO: get the list of packages from a text file.
    packages_str = " ".join([p for p in packages()])
    run("sudo apt-get --yes --force-yes install " + packages_str)
    #run("sudo apt-get --yes --force-yes build-dep python-numpy")
    ensure_src_dir()
    with settings(warn_only=True):
        ssh_keygen(env.project_name) 
            
@task
def deploy():
    """ Deploy the toolkit to a remote server.
    """
    with settings(warn_only=True):
        fetch_stop()
    push_sources()
    install_dependencies()
    

@task
def memory_usage():
    """ Get the server's mem usage
    """ 
    run('free -m')
