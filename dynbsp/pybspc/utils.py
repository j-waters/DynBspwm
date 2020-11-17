from dataclasses import dataclass
from json import loads
from logging import error
from subprocess import Popen, PIPE

INVCHAR = "\u200B"


class Process:
	def __init__(self, process: Popen):
		self.process = process

	def read(self):
		return self.process.stdout.read().strip().decode('utf-8')

	def json(self):
		return loads(self.read())

	def readline(self):
		return self.process.stdout.readline().strip().decode('utf-8')

	def wait(self, timeout=None):
		self.process.wait(timeout)
		err = self.error()
		if err:
			error(err)

	def error(self):
		if self.process.stderr is None:
			return None
		return self.process.stderr.read().strip().decode('utf-8')


def run(*args, wait=True, debug=False):
	command = []
	for arg in args:
		command.extend(arg.split(" "))
	command = list(map(lambda c: c.replace('\S', ' '), command))
	if debug:
		print("Running:", args, "->", list(command))
	process = Process(Popen(command, stdout=PIPE))
	if wait: process.wait()
	return process


def _int(i):
	if type(i) == str:
		return int(i, 0)
	return int(i)


@dataclass
class Rect:
	x: int
	y: int
	width: int
	height: int


@dataclass
class Padding:
	top: int
	right: int
	bottom: int
	left: int
