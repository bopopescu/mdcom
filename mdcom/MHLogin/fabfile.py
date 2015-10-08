import os
from datetime import datetime

from settings import PROJECT_NAME, PROJECT_ROOT as DEV_PROJECT_ROOT, DATABASES
from django.conf import settings

from fabric.api import local, run, cd, env, sudo, get
from fabric.contrib.console import confirm
from fabric.decorators import runs_once


#PROJECT_NAME = 'doctorcom'

DEFAULT_DB_SETTINGS = settings.DATABASES['default']
if not DEFAULT_DB_SETTINGS['PASSWORD']:
    MYSQL_USER_PASSWD = 'mysql -u%s' % DEFAULT_DB_SETTINGS['USER']
else:
    MYSQL_USER_PASSWD = 'mysql -u%s -p%s' % (DEFAULT_DB_SETTINGS['USER'], DEFAULT_DB_SETTINGS['PASSWORD'])
MYSQL_EXEC_CMD = '%s -e' % MYSQL_USER_PASSWD

def prod():
    """Sets up the prod environment for fab remote commands"""
    from settings.prod import SSH_HOSTS
    env.user = 'USERNAME'
    env.hosts = SSH_HOSTS
    
    env.CODE_DIR = '/home/YOURSITE/src/%s/' % (PROJECT_NAME)
def fulllaunch():
    """Launch new code. Does a git pull, migrate and bounce"""
    from settings.prod import DATABASES
    
    # take a db dump
    DUMP_FILENAME = 'launchdump-%s.sql.gz' % datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    run( 'mysqldump -u%s -p%s %s | gzip > /tmp/%s' % (DATABASES['default']['USER'],\
        DATABASES['default']['PASSWORD'], DATABASES['default']['NAME'], DUMP_FILENAME))
    
    with cd(env.CODE_DIR):
        _run_in_ve('git pull')
        _run_in_ve('sudo pip install -r requirements.pip') #dont' need to run it every time
        migrate()
        _run_in_ve('python manage.py collectstatic --noinput')
        _run_in_ve('sudo find . -name \*.pyc -delete')
    
    bounce()

def launch():
    """Launch new code. Does a git pull, migrate and bounce"""
    #from settings.prod import DATABASES
    
    # take a db dump
    #DUMP_FILENAME = 'launchdump-%s.sql.gz' % datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    #run( 'mysqldump -u%s -p%s %s | gzip > /tmp/%s' % (DATABASES['default']['USER'],\
    #    DATABASES['default']['PASSWORD'], DATABASES['default']['NAME'], DUMP_FILENAME))
    
    with cd(env.CODE_DIR):
        #_run_in_ve('git pull')
        _run_in_ve('python manage.py collectstatic --noinput')
        _run_in_ve('sudo find . -name \*.pyc -delete')
    
    bounce()

@runs_once
def migrate():
    """Does a syncdb, a dry run of migrate and a real migration if that suceeds."""
    with cd(env.CODE_DIR):
        _run_in_ve('python manage.py syncdb --noinput')
        _run_in_ve('python manage.py migrate --db-dry-run --noinput')
        _run_in_ve('python manage.py migrate --noinput')

def bounce():
    """Bounce apache + memcache"""
    sudo('/etc/init.d/apache2 restart', pty=False)
    sudo('/etc/init.d/memcached restart', pty=False)
    _run_in_ve('/etc/init.d/celeryd restart')

def syncdb():
    """Gets a copy of the remote db and puts it into dev environment"""
    from settings.prod import DATABASES
    DUMP_FILENAME = 'dump-%s.sql.gz' % datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    DUMP_FILENAME_SQL = DUMP_FILENAME[:-3]
    
    if confirm('This may replace your db (you will get opportunity to specify which one). You sure?'):
        run( 'mysqldump -u%s -p%s %s | gzip > /tmp/%s' % (DATABASES['default']['USER'],\
            DATABASES['default']['PASSWORD'], DATABASES['default']['NAME'], DUMP_FILENAME)) # dump and gzip db
        get('/tmp/%s' % DUMP_FILENAME, os.path.basename(DUMP_FILENAME)) # download db
        local('gzip -d %s' % os.path.basename(DUMP_FILENAME)) # ungzip
        freshdb()
        local('%s %s < %s' % (MYSQL_USER_PASSWD, DEFAULT_DB_SETTINGS['NAME'], DUMP_FILENAME_SQL))
        local('rm %s' % DUMP_FILENAME_SQL)

def _run_in_ve(command):
    run('workon %s; cd %s; %s' % (PROJECT_NAME, env.CODE_DIR, command))


####
# dev specific fab commands
####
def freshdb():
    #if not settings.IS_DEV:
    #    raise Exception('This command is to only run on DEV')

    env.warn_only = True #so fab doesnt drop out if the db doesnt exist yet.
    local('%s "%s"' % (MYSQL_EXEC_CMD, 'drop database %s' % DEFAULT_DB_SETTINGS['NAME']))
    env.warn_only = False
    local('%s "%s"' % (MYSQL_EXEC_CMD, 'create database %s DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci' %\
        DEFAULT_DB_SETTINGS['NAME']))
def loaddata():
    local('%s %s < %s' % (MYSQL_USER_PASSWD, DEFAULT_DB_SETTINGS['NAME'], "../mhlogin_dump.sql"))
    local('%s %s < %s' % (MYSQL_USER_PASSWD, DEFAULT_DB_SETTINGS['NAME'], "../alters.sql"))

def update(syncdb=True):
    if not settings.IS_DEV:
        raise Exception('This command is to only run on DEV')
    
    with cd(DEV_PROJECT_ROOT):
        #local('git pull')
        _local_in_ve('pip install -r requirements.pip')
        if syncdb:
            _local_in_ve('python manage.py syncdb --noinput')
            _local_in_ve('python manage.py migrate --db-dry-run --noinput')
            _local_in_ve('python manage.py migrate --noinput')
def local_migrate():
    _local_in_ve('python manage.py syncdb --noinput')
    _local_in_ve('python manage.py migrate --db-dry-run --noinput')
    _local_in_ve('python manage.py migrate --noinput')
    
def bootstrap():
    """Bootstraps a dev box. Drops/creates db, installs requirements, does syncdb/migrate etc. Should also obfuscate
    real user emails (using django-extensions command) and also change site string in db to localhost?"""
    if confirm('This will blow up your env setup. You sure?'):
        with cd(DEV_PROJECT_ROOT):
            pass
            #local('git pull')
        freshdb()
        update()
def sphinxdocs():
    """Generates sphinx html locally"""
    local('cd genbilling/docs; rm -rf build; make html')
def runtests():
    local('python manage.py test genbilling -v2')


def graphmodels():
    """Do 'pip install pygraphviz'. It'll give an error. Go into the source (in the $VIRTUAL_ENV/build/pygraphviz/setup.py
    file) and comment out and replace with these 2 lines:
    
    #library_path=None
    #include_path=None
    library_path='/usr/local/lib/graphviz'
    include_path='/usr/local/include/graphviz'
    
    This assumes you have graphviz installed (via macports or brew) of course.
    
    Do a 'pip install pygraphviz' again.
    """
    _local_in_ve('python manage.py graph_models -a -g -o graphed_models.png')

def _local_in_ve(command):
    local('workon %s; cd %s; %s' % (PROJECT_NAME, DEV_PROJECT_ROOT, command), capture=False)
    
@runs_once    
def sync():
    syncdb()
    sync_uploads()

@runs_once
def sync_uploads():
    """ Reset local media from remote host """
    local("sudo rsync -rva USER@%s:YOURSITE/src/%s/uploads/ uploads" % (env.host_string,PROJECT_NAME))
