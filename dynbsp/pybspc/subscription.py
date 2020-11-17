import traceback
from logging import debug, info, warning

from .bspwm import BSPWM
from .utils import run


class Subscriber:
	def __init__(self):
		self.subscription = run('bspc subscribe all', wait=False)
		self.events = {}

	def poll(self):
		try:
			return self.subscription.readline()
		except KeyboardInterrupt:
			exit()
		except UnicodeDecodeError:
			return ""

	def listen(self):
		while True:
			message = self.poll()
			if message.split(' ')[0] in self.events.keys():
				self.handle(message)
			else:
				continue
				debug(f"Unhandled message: {message}")

	def handle(self, message):
		try:
			message = message.split(' ')
			action = message[0]
			info(f"Handling action: {action}")
			wm = BSPWM.get()
			if action == 'node_add':
				# monitor_id    desktop_id  ip_id   node_id
				monitor = wm.get_monitor(message[1])
				desktop = wm.get_desktop(message[2])
				node = wm.get_node(message[4])
				self.events.get(action)(wm, monitor, desktop, node)
			if action == 'node_remove':
				# monitor_id    desktop_id   node_id
				monitor = wm.get_monitor(message[1])
				desktop = wm.get_desktop(message[2])
				node = wm.get_node(message[3])
				self.events.get(action)(wm, monitor, desktop, node)
			if action == 'desktop_transfer':
				# src_monitor_id src_desktop_id dst_monitor_id
				src_monitor = wm.get_monitor(message[1])
				src_desktop = wm.get_desktop(message[2])
				dst_monitor = wm.get_monitor(message[3])
				self.events.get(action)(wm, src_monitor, src_desktop, dst_monitor)
			if action == 'desktop_remove':
				# <monitor_id> <desktop_id>
				monitor = wm.get_monitor(message[1])
				desktop = wm.get_desktop(message[2])
				self.events.get(action)(wm, monitor, desktop)
			if action == 'node_transfer':
				# <src_monitor_id> <src_desktop_id> <src_node_id>
				# <dst_monitor_id> <dst_desktop_id> <dst_node_id>
				src_monitor = wm.get_monitor(message[1])
				src_desktop = wm.get_desktop(message[2])
				src_node = wm.get_node(message[3])
				dst_monitor = wm.get_monitor(message[4])
				dst_desktop = wm.get_desktop(message[5])
				dst_node = wm.get_node(message[6])
				self.events.get(action)(wm, src_monitor, src_desktop, src_node, dst_monitor, dst_desktop, dst_node)
			if action == 'monitor_remove':
				# <monitor_name>
				pass
			if action == 'monitor_add':
				# <monitor_id> <monitor_name> <monitor_geometry>
				monitor = wm.get_monitor(message[1])
				self.events.get(action)(wm, monitor)

		except Exception as e:
			warning("Exception caught while handling '" + " ".join(message) + "'")
			traceback.print_exc()
			print("MESSAGE:", message)

	def event(self, event_str):
		def decorator(f):
			self.events[event_str] = f
			return f

		return decorator
