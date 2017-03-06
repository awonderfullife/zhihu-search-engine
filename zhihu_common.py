import subprocess

def exec_in_new_console(cmd, stdout = None, stderr = None):
	return subprocess.Popen(('gnome-terminal', '-x') + cmd, stdout = stdout, stderr = stderr)

class external_console_logger:
	def __init__(self, logfile, mode = 'w'):
		self._file = open(logfile, mode)
		self._disp = exec_in_new_console(('tail', '-f', logfile), stdout = open('/dev/null', 'w'), stderr = open('/dev/null', 'w'))

	def write(self, s):
		if isinstance(s, unicode):
			self._file.write(s.encode('utf8'))
		else:
			self._file.write(s)
		self._file.flush()
