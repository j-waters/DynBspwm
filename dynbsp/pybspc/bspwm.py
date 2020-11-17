from json import loads
from json.decoder import JSONDecodeError
from logging import error
from typing import Set

from .desktop import Desktop
from .monitor import Monitor
from .node import Node
from .utils import run, _int


class BSPWM:
	def __init__(self, data):
		self.data = data
		self.monitors = set()

		for monitor in data["monitors"]:
			self.monitors.add(Monitor(monitor))

	@staticmethod
	def get():
		inp = run("bspc wm -d").read()
		try:
			data = loads(inp)
		except JSONDecodeError as e:
			error("Error reading JSON:")
			error(inp)
			raise e

		return BSPWM(data)

	@property
	def nodes(self) -> Set[Node]:
		return set().union(*(d.nodes for d in self.desktops))

	@property
	def desktops(self) -> Set[Desktop]:
		return set().union(*(m.desktops for m in self.monitors))

	@property
	def current_monitor(self):
		monitor_id = self.data["focusedMonitorId"]
		return self.get_monitor(monitor_id)

	def get_monitor(self, monitor_id):
		monitor_id = _int(monitor_id)
		return next((monitor for monitor in self.monitors if monitor.id == monitor_id), None)

	def pretty_print(self, indent=0):
		print("|\t" * indent, f"<BSPWM monitors: [", sep="")
		for monitor in self.monitors:
			monitor.pretty_print(indent=indent + 1)
		print("|\t" * indent, "]>", sep="")

	def get_desktop(self, desktop_id):
		desktop_id = _int(desktop_id)
		return next((desktop for desktop in self.desktops if desktop.id == desktop_id), None)

	def get_node(self, node_id):
		node_id = _int(node_id)
		return next((node for node in self.nodes if node.id == node_id), None)
