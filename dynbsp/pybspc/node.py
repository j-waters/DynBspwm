from typing import TYPE_CHECKING, Union

from .utils import run

if TYPE_CHECKING:
	from .desktop import Desktop


class Node:
	def __init__(self, data, desktop: Union["Desktop", "Node"]):
		self.data = data
		self.desktop = desktop
		self.client = Client(data["client"]) if data["client"] is not None else None
		self.first_child = Node.instantiate(self.data["firstChild"], self)
		self.second_child = Node.instantiate(self.data["secondChild"], self)

	@staticmethod
	def instantiate(data, desktop: Union["Desktop", "Node"]):
		if data is None:
			return None
		return Node(data, desktop)

	@property
	def id(self):
		return self.data["id"]

	@property
	def children(self):
		children = set()
		if self.first_child:
			children.add(self.first_child)
			children = children.union(self.first_child.children)
		if self.second_child:
			children.add(self.second_child)
			children = children.union(self.second_child.children)
		return children

	def to_desktop(self, desktop: "Desktop", follow=True):
		run(f'bspc node {self.id} --to-desktop {desktop.id} {"--follow" if follow else ""}')

	def __repr__(self):
		return f"<Node id: {self.id}, client: {self.client}>"

	def pretty_print(self, indent=0):
		print("|\t" * indent, f"<Node id: {self.id}, client: {self.client}, children: [", sep="", end="")
		if self.first_child is None and self.second_child is None:
			print("]>")
		else:
			print()
			if self.first_child:
				self.first_child.pretty_print(indent=indent + 1)
			if self.second_child:
				self.second_child.pretty_print(indent=indent + 1)
			print("|\t" * indent, "]>", sep="")


class Client:
	def __init__(self, data):
		self.data = data

	@property
	def class_name(self):
		return self.data.get("className", None)

	@property
	def instance_name(self):
		return self.data.get("instanceName", None)

	def __repr__(self):
		return f"<Client class: {self.class_name}>"
