from subprocess import Popen, PIPE
from json import loads
from random import randint
import traceback
from sys import exit
import inspect
import logging

INVCHAR = "\u200B"


class DesktopNotFound(Exception):
	pass


class Desktop:
	def __init__(self, selector):
		self.selector = selector
		self.query()

	def query(self):
		proc = run('bspc query --tree -d {}'.format(self.selector))
		data = proc.stdout.readline().strip()
		try:
			data = data.decode('utf-8').replace('\\', '\\\\')
		except UnicodeDecodeError:
			print("Cannot decode", data)
			self.remove()
			return
		if data.split(':')[0] == "query -d":
			raise DesktopNotFound()
		self.data = loads(data)
		self.selector = self.id

	def remove(self):
		run('bspc desktop {} --remove'.format(self.selector))

	def rename(self, name):
		run('bspc desktop {} --rename {}'.format(self.selector, name))
		self.data['name'] = name

	def get_nodes(self):
		proc = run('bspc query --nodes --node .window --desktop {}'.format(self.selector))
		data = proc.stdout.read().strip().decode('utf-8')
		if data[:5] == 'query':
			self.remove()
			return []
		return [Node(sel) for sel in data.split('\n') if sel != '']

	def __getattr__(self, name):
		return getattr(self, 'data').get(name)

	def __repr__(self):
		return "<Desktop {}>".format(self.name)


class Node:
	def __init__(self, selector):
		self.selector = selector
		self.data = {}
		self.className = None
		self.query()

	def query(self):
		proc = run('bspc query --node {} --tree'.format(self.selector))
		data = proc.stdout.readline().strip().decode('utf-8')
		try:
			self.data = loads(data)
		except Exception as e:
			print("====")
			print(data)
			raise e
		self.className = self.data['client']['className']
		self.selector = self.id

	def to_desktop(self, desktop, follow=True):
		run("bspc node {} --to-desktop {} {}".format(self.selector, desktop.selector, '--follow' if follow else ''))

	def __getattr__(self, name):
		return self.data.get(name)

	def __repr__(self):
		return "<Node {}>".format(self.className)


class Monitor:
	def __init__(self, selector):
		self.selector = selector
		self.query()

	def query(self):
		if self.exists():
			proc = run('bspc query --monitors --monitor {}'.format(self.selector))
			self.selector = proc.stdout.read().strip().decode('utf-8')

	def create(self, rect):
		run("bspc wm --add-monitor {} {}".format(self.selector, rect))

	def exists(self):
		proc = run("bspc query --monitors --monitor {}".format(self.selector))
		out = proc.stdout.read().strip().decode('utf-8')
		if "Invalid descriptor" in out:
			return False
		return True

	def get_desktops(self):
		proc = run('bspc query --desktops --monitor {}'.format(self.selector))
		data = proc.stdout.read().strip().decode('utf-8')
		if data[:5] == 'query':
			self.remove()
			return []
		return [Desktop(sel) for sel in data.split('\n') if sel != '']

	def add_desktop(self, name):
		tmp = randint(0, 9) * INVCHAR
		run('bspc monitor {} -a {}'.format(self.selector, tmp))
		desk = Desktop(tmp)
		desk.rename(name)
		return desk

	def move_all(self, monitor, leftover="", exclude=[]):
		desktops = self.get_desktops()
		print("moving desktops", desktops)
		for desktop in desktops:
			if desktop.name not in exclude:
				print("moving", desktop)
				proc = run('bspc desktop {} --to-monitor {}'.format(desktop.selector, monitor.selector))
		self.add_desktop(leftover)

	def swap(self, monitor):
		proc = run('bspc monitor --swap {}'.format(monitor.selector))

	def rectangle(self, x, y, w, h):
		proc = run('bspc monitor --rectangle {}x{}+{}+{}'.format(w, h, x, y))

	def remove(self):
		run('bspc monitor {} --remove'.format(self.selector))


class Subscriber:
	def __init__(self):
		self.subscription = run('bspc subscribe all', wait=False)
		self.events = {}

	def poll(self):
		try:
			return self.subscription.stdout.readline().strip().decode('utf-8')
		except KeyboardInterrupt:
			exit()
		except UnicodeDecodeError:
			return ""

	def listener(self):
		while True:
			message = self.poll()
			logging.debug(">>>" + message)
			if message.split(' ')[0] in self.events.keys():
				self.handle(message)

	def handle(self, message):
		try:
			message = message.split(' ')
			action = message[0]
			logging.info("Handling action: " + action)

			if action == 'node_add':
				# monitor_id    desktop_id  ip_id   node_id
				node = Node(message[4])
				desktop = Desktop(message[2])
				self.events.get(action)(node, desktop)
			if action == 'node_remove':
				# monitor_id    desktop_id   node_id
				desktop = Desktop(message[2])
				self.events.get(action)(desktop)
				pass
			if action == 'desktop_transfer':
				# src_monitor_id src_desktop_id dst_monitor_id
				desktop = Desktop(message[1])
				self.events.get(action)(desktop)
			if action == 'node_transfer':
				# <src_monitor_id> <src_desktop_id> <src_node_id>
				# <dst_monitor_id> <dst_desktop_id> <dst_node_id>
				self.events.get(action)()

		except Exception as e:
			logging.warn("Exception caught while handling '" + " ".join(message) + "'")
			traceback.print_exc()
			print("MESSAGE:", message)

	def event(self, event_str):
		def decorator(f):
			self.events[event_str] = f
			return f

		return decorator


def run(*args, wait=True):
	command = []
	for arg in args:
		command.extend(arg.split(" "))
	for i in range(len(command)):
		command[i] = command[i].replace('\S', ' ')
	proc = Popen(command, stdout=PIPE)
	if wait: proc.wait()
	return proc


def add_desktop(name):
	# fixes issues with duplicate names
	tmp = randint(0, 9) * INVCHAR
	run('bspc monitor -a {}'.format(tmp))
	desk = Desktop(tmp)
	desk.rename(name)
	return desk


def get_desktops():
	proc = run('bspc query --desktops')
	data = proc.stdout.read().strip().decode('utf-8')
	desktops = [Desktop(sel) for sel in data.split('\n')]
	return desktops


def get_monitors():
	proc = run('bspc query --monitors')
	data = proc.stdout.read().strip().decode('utf-8')
	monitors = [Monitor(sel) for sel in data.split('\n')]
	return monitors


def reorder(desktops):
	c = 0
	names = []
	old = []
	for desktop in desktops:
		# fixes issues with duplicate names
		new = desktop.name + c * INVCHAR
		c += 1
		old.append(desktop.name)
		desktop.rename(new)
	p = run(
		'bspc monitor --reorder-desktops {}'.format(" ".join([str(desk.name).replace(' ', '\S') for desk in desktops])))
	for i in range(len(desktops)):
		desktops[i].rename(old[i].replace(' ', '\S'))
