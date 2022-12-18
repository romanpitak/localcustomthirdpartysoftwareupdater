import argparse
import git
import logging
from logging import debug, info, warning, error
import os
import pkg_resources
import requests
import simplejson as json
import tarfile
import time
import urllib.parse


class Sw:
	_short_name = None

	def update(self):
		raise NotImplementedError()

	@classmethod
	def short_name(cls):
		if cls._short_name is None:
			raise NotImplementedError()
		return cls._short_name


class _GitBased(Sw):

	class MyProgressPrinter(git.RemoteProgress):
		def update(self, op_code, cur_count, max_count=None, message=''):
			print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")

	def update(self):
		repo = git.Repo(os.sep.join([os.path.expanduser('~'), 'opt', self.short_name()]))
		assert not repo.bare
		info('FETCH')
		for fetch_info in repo.remote().fetch(progress=self.MyProgressPrinter()):
			debug("Updated %s to %s" % (fetch_info.ref, fetch_info.commit))
		info('PULL')
		for fetch_info in repo.remote().pull(progress=self.MyProgressPrinter()):
			debug("Updated %s to %s" % (fetch_info.ref, fetch_info.commit))


class Pyenv(_GitBased):
	_short_name = 'pyenv'


class Phpenv(_GitBased):
	_short_name = 'phpenv'
	# TODO php-build


class _JetBrains(Sw):

	_CODE = None
	_DOT_DIR = None
	_latest_release = None

	def __init__(self):
		self._install_path = os.sep.join([os.path.expanduser('~'), 'opt'])

	def latest_version(self):
		return self._get_latest_release()['build']

	def installed_version(self):
		return self._installed_versions()[-1]

	def _installed_versions(self):

		def _extract_version(file_name):
			with open(file_name, 'r') as file_handle:
				return pkg_resources.parse_version(file_handle.readlines()[0].split('-', 1)[1])

		return [str(x) for x in sorted([
			_extract_version(install_path + '/build.txt')
			for install_path in (
				self._install_path + os.sep + dir_name
				for dir_name in os.listdir(self._install_path)
			)
			if os.path.isdir(install_path) and self._is_my_installed_path(install_path)
		])]

	def _is_my_installed_path(self, path):
		return os.path.isfile(path + '/bin/' + self.short_name() + '.sh')

	def _pull_latest_release(self):
		url = 'https://data.services.jetbrains.com/products/releases?' + urllib.parse.urlencode([
			('code', self._CODE),
			('latest', 'true'),
			('type', 'release'),
			('_', int(1000 * time.time())),
		])
		response = requests.get(url)
		document = json.loads(response.content)
		debug('Latest release info: %s', document)
		return document[self._CODE][0]

	def _get_license_file_name(self):
		return [
			file_name
			for file_name in os.listdir(os.sep.join([
				os.path.expanduser('~'),
				self._DOT_DIR,
				'config', 'eval'
			]))
			if file_name.endswith('.evaluation.key')
		][0]

	def _get_latest_release(self):
		if self._latest_release is None:
			self._latest_release = self._pull_latest_release()

		return self._latest_release

	def _pull_latest_file(self):
		url = self._get_latest_release()['downloads']['linux']['link']
		file_size = float(self._get_latest_release()['downloads']['linux']['size'])
		file_name = url.rsplit('/', 1)[-1]
		response = requests.get(url, stream=True)
		with open(file_name, 'wb') as file_handle:
			chunk_size = 2**20
			for chunk_index, chunk in enumerate(response.iter_content(chunk_size=chunk_size), start=1):
				file_handle.write(chunk)
				debug('finished %s%%', str(round(100 * chunk_index * chunk_size / file_size, 2)))
		with tarfile.open(file_name, mode='r:gz') as tar_file_handle:
			tar_dir = tar_file_handle.next().name.split('/', 1)[0]
			debug('tar dir: "%s"', tar_dir)
			info('Extracting "%s" to "%s"', file_name, self._install_path)
def is_within_directory(directory, target):
	
	abs_directory = os.path.abspath(directory)
	abs_target = os.path.abspath(target)

	prefix = os.path.commonprefix([abs_directory, abs_target])
	
	return prefix == abs_directory

def safe_extract(tar, path=".", members=None, *, numeric_owner=False):

	for member in tar.getmembers():
		member_path = os.path.join(path, member.name)
		if not is_within_directory(path, member_path):
			raise Exception("Attempted Path Traversal in Tar File")

	tar.extractall(path, members, numeric_owner=numeric_owner) 
	

safe_extract(tar_file_handle, path=self._install_path)
		link_name = os.path.expanduser('~') + '/bin/' + self.short_name()
		if os.path.exists(link_name):
			debug('Removing link "%s"', link_name)
			if not os.path.islink(link_name):
				error('Aborted! Not a link! "%s"', link_name)
				return False
			os.remove(link_name)
		os.symlink('../opt/' + tar_dir + '/bin/' + self.short_name() + '.sh', link_name)

	def update_available(self):
		latest = pkg_resources.parse_version(self.latest_version())
		installed = pkg_resources.parse_version(self.installed_version())
		return latest > installed

	def update(self):
		if not self.update_available():
			info('Already on the latest version: "%s"', self.latest_version())
			debug('latest: "%s", installed: "%s"', self.latest_version(), self.installed_version())
			return True
		info('Installing version "%s"', self.latest_version())
		return self._pull_latest_file()


class Clion(_JetBrains):

	_short_name = 'clion'

	_CODE = 'CL'

	def __init__(self):
		super().__init__()
		self._DOT_DIR = '.CLion' + self.installed_version()  # TODO wont work


class PhpStorm(_JetBrains):

	_short_name = 'phpstorm'

	_CODE = 'PS'

	def __init__(self):
		super().__init__()
		self._DOT_DIR = '.PhpStorm' + self.installed_version()  # TODO


class PycharmCommunity(_JetBrains):

	_short_name = 'pycharm'

	_CODE = 'PCC'

	def __init__(self):
		super().__init__()
		self._DOT_DIR = '.PyCharm' + self.installed_version()  # TODO

	def renew_eval(self):
		return True


class WebStorm(_JetBrains):

	_short_name = 'webstorm'

	_CODE = 'WS'

	def __init__(self):
		super().__init__()
		self._DOT_DIR = '.WebStorm' + self.installed_version()  # TODO


available_sw = [Clion, PhpStorm, PycharmCommunity, WebStorm, Pyenv, Phpenv]


def main():
	parser = argparse.ArgumentParser(description='Update third party software')

	parser.add_argument('-v', '--verbose', action='count')

	# TODO http://bugs.python.org/issue9625
	# parser.add_argument('update', choices=[x.short_name for x in available_sw], nargs='*')
	parser.add_argument('update', choices=['ALL'] + [x.short_name() for x in available_sw] + ['--'], nargs='*', default='--')

	parser.add_argument('--autocomplete', action='store_true')

	c = parser.parse_args()

	# TODO http://bugs.python.org/issue9625
	if '--' == c.update:
		c.update = []
	elif 'ALL' in c.update:
		c.update = [x.short_name() for x in available_sw]

	if c.verbose is None:
		logging.basicConfig(level=logging.WARNING)
	elif 1 == c.verbose:
		logging.basicConfig(level=logging.INFO)
	else:
		logging.basicConfig(level=logging.DEBUG)

	debug('CONFIG: %s', c)

	if c.autocomplete is True:
		fname = '_localcustomthirdpartysoftwareupdates_autocomplete'
		choices = ' '.join([x.short_name for x in available_sw] + ['-v', '-vv'])
		print(''.join([
			fname, '(){ ',
			'COMPREPLY=( $(compgen -W "', choices, '" -- "${COMP_WORDS[COMP_CWORD]}") ); return 0; }; ',
			'complete -F ', fname, ' update'
		]))
		exit()
	elif c.update:
		available_sw_map = {sw.short_name(): sw for sw in available_sw}
		for sw_class in (available_sw_map[sw] for sw in list(set(c.update))):
			info('Updating %s', sw_class.short_name())
			sw = sw_class()
			info(sw.update())
	else:
		parser.print_help()


if '__main__' == __name__:
	main()
