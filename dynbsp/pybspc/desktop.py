from typing import Set, TYPE_CHECKING

from .node import Node
from .utils import run, _int

if TYPE_CHECKING:
	from .monitor import Monitor


class DesktopNotFound(Exception):
	pass


class Desktop:
	def __init__(self, data, monitor: "Monitor"):
		self.data = data
		self.monitor = monitor
		self.root = Node.instantiate(self.data["root"], self)

	@property
	def id(self):
		return self.data["id"]

	@property
	def name(self):
		return self.data["name"]

	@property
	def nodes(self) -> Set[Node]:
		return {self.root}.union(self.root.children) if self.root is not None else set()

	def get_node(self, node_id):
		node_id = _int(node_id)
		return next((node for node in self.nodes if node.id == node_id), None)

	@property
	def current_node(self):
		node_id = self.data["focusedNodeId"]
		return self.get_node(node_id)

	def __repr__(self) -> str:
		return f"<Desktop id: {self.id}, name: {self.name}>"

	def pretty_print(self, indent=0):
		print("|\t" * indent, f"<Desktop id: {self.id}, name: {self.name}, root: ", sep="")
		if self.root:
			self.root.pretty_print(indent=indent + 1)
		print("|\t" * indent, ">", sep="")

	def rename(self, name: str):
		removed_spaces = name.replace(" ", "\S")
		run(f'bspc desktop {self.id} --rename {removed_spaces}')
		self.data['name'] = name

	def delete(self):
		run(f'bspc desktop {self.id} --remove')

	def swap(self, desktop, follow=False):
		run(f'bspc desktop {self.id} --swap {desktop.id} {"--follow" if follow else ""}')

	def to_monitor(self, monitor: "Monitor", follow=False):
		run(f'bspc desktop {self.id} --to-monitor {monitor.id} {"--follow" if follow else ""}')

	@staticmethod
	def get(selector):
		proc = run(f"bspc query --desktop {selector} --tree")
		return Desktop(proc.json(), None)
