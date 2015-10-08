
import re
import sys
from optparse import OptionParser
from os.path import join, dirname, abspath
from subprocess import Popen, PIPE

# cygwin uses git, only git.cmd for bill
gitcmd = 'git.cmd' if sys.platform in ('win32', 'win64') else 'git'
# default arguments we passing to git:
gitargs = [gitcmd, 'describe', '--tags', '--always', '--dirty']
# default git tag regex to pickup version and optional date from git describe output
tag_re = 'version/(?P<date>(\d{4}-\d{2}-\d{2})?)-?\.?'\
	'(?P<version>(\*|\d+(\.\d+){0,3}(\.\*)?))-?(?P<gitmeta>.*)$'
# what will be our _version.py file:
VERSION_PY = \
'''
# _version.py generated from git metadata via setup.py

__version__ = '%(version)s'
__gitmeta__ = '%(gitmeta)s'  # remaining metadata from tag if any

'''


def get_version_from_git(opts):
	""" Fetches recent git tag labeled for production and extract version """
	stdout = opts.tag or Popen(gitargs, stdout=PIPE).communicate()[0].rstrip('\n')

	version, gitmeta = process_git_tag(opts.regex, stdout)

	return version, gitmeta


def create_version_file(version='unknown', gitmeta=''):
	""" Create the _version.py file with __version__ declared """
	fname = join(dirname(abspath(__file__)), 'MHLogin', '_version.py')
	f = open(fname, 'wb')
	f.write(VERSION_PY % {'version': version, 'gitmeta': gitmeta, })
	f.close()


def dry_run(opts, output=sys.stderr):
	""" Dry run based on options (for test) """
	output.write('input: %s\n' % (' '.join(gitargs)))
	stdout = opts.tag or Popen(gitargs, stdout=PIPE).communicate()[0].rstrip('\n')
	output.write('output: %s\n\n' % (stdout))
	output.write('regex input: %s\n' % (opts.regex))

	version, gitmeta = process_git_tag(opts.regex, stdout)
	output.write('version output: %s\n' % (version))
	output.write('gitmeta output: %s\n\n' % (gitmeta))


def process_git_tag(regex, inputtag):
	""" Process git tag and return cleaned version, gitmeta """
	try: 
		gitre = re.compile(regex)
		match = gitre.search(inputtag)
		groups = match.groupdict()
		version = groups.get('version', '.unknown')
		date = groups.get('date', '')
		gitmeta = groups.get('gitmeta', '')
		if date:
			version = '.'.join([version, ''.join(date.split('-'))])
	except (AttributeError, EnvironmentError, OSError):
		version, gitmeta = '.unknown', ''

	return version, gitmeta


if __name__ == '__main__':
	usage = """usage: %prog [options]
	Generate version string in <project>/_version.py from recent git tag, eg:
		$ python setup.py
		Note: setup.py is assumed to run on the git branch you extract tag  
		from.  If on a different branch specify -b<branch_name> as option.
		Git tag should be in the form "version/yyyy-mm-dd-x.y.z..."
		$ git describe --tags --dirty --always
		version/2013-02-14-1.60.10-09-gcf899cc-dirty
		or:
		version/1.60.10.20130214-09-gcf899cc-dirty
	to <project>/_version.py:
		__version__ = '1.60.10.20130214'  
	"""
	parser = OptionParser(usage)
	parser.add_option('-p', '--reg-prefix', action='store', dest='regex', 
		default=tag_re, help='Regular expression prefix to extract version from '
			'tag. Named group (?P<version>...) must be present. default: %default')
	parser.add_option('-d', '--dry-run', action='store_true', dest='dryrun', 
		default=False, help='Dry run, only print git metadata results and ' 
			'version output, default: %default')
	parser.add_option('-t', '--tag-override', action='store', dest='tag', 
		default=None, help='Override git tag used for test, '
			'default: %default', metavar='your_gittag')
	parser.add_option('-b', '--branch', action='store', dest='branch', 
		default=None, help='Override git branch used to search for tag, '
			'default: %default, <none is current branch>', metavar='git_branch')

	(opts, args) = parser.parse_args()

	if len(args) == 0:
		if opts.branch:
			gitargs.pop(-1)  # remove the dirty option when giving branch name
			gitargs.append(opts.branch)

		if opts.dryrun:
			dry_run(opts)
		else:
			version, gitmeta = get_version_from_git(opts)
			create_version_file(version, gitmeta) 
	else:
		parser.print_help()


#sample of expected tags:
#	prod_version/1.60.10.20130214-42-gcf899cc-dirty
#	version/2013-02-14-1.60.60-42-gcf899cc-dirty
#Some notes from Thorsten:
#suggested tag format:
#	version/yyyy-mm-dd-x.y.z"+ git tag metata and strip out that metadata:
#	-[:digit:]]+-g[[:hexdigit:]]+" suffix.
#	or...:
#	production/yyyy-mm-dd-x.y.z"+ git tag metata
#

