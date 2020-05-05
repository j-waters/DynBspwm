from random import randint
from typing import Union, Set, List, Tuple

from .node import Node
from .desktop import Desktop
from .utils import run, INVCHAR, _int


class Monitor:
	def __init__(self, data):
		self.data = data
		self.desktops = []
		for desktop in data["desktops"]:
			self.desktops.append(Desktop(desktop, self))

	@property
	def id(self):
		return self.data["id"]

	@property
	def name(self):
		return self.data["name"]

	@property
	def current_desktop(self):
		desktop_id = self.data["focusedDesktopId"]
		return self.get_desktop(desktop_id)

	@property
	def nodes(self) -> Set[Node]:
		return set().union(*(d.nodes for d in self.desktops))

	def create_desktop(self, name):
		temp_name = INVCHAR
		run(f'bspc monitor {self.id} --add-desktops {temp_name}')
		desktop = Desktop.get(temp_name)
		desktop.rename(name)
		return desktop

	def __repr__(self) -> str:
		return f"<Monitor id: {self.id}, name: {self.name}>"

	def pretty_print(self, indent=0):
		print("|\t" * indent, f"<Monitor id: {self.id}, name: {self.name}, desktops: [", sep="")
		for desktop in self.desktops:
			desktop.pretty_print(indent=indent + 1)
		print("|\t" * indent, "]>", sep="")

	def get_desktop(self, desktop_id):
		desktop_id = _int(desktop_id)
		return next((desktop for desktop in self.desktops if desktop.id == desktop_id), None)

	def get_node(self, node_id):
		node_id = _int(node_id)
		return next((node for node in self.nodes if node.id == node_id), None)

	def reorder(self, ordered_desktops: List[Desktop]):
		operations: List[Tuple[Desktop, Desktop]] = []
		working = self.desktops.copy()
		for i in range(len(working)):
			current_desktop = working[i]
			target_index = ordered_desktops.index(current_desktop)
			target_desktop = working[target_index]
			operations.append((current_desktop, target_desktop))
			working[i] = target_desktop
			working[target_index] = current_desktop

		for operation in operations:
			operation[0].swap(operation[1])
