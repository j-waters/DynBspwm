from enum import Enum
from typing import TYPE_CHECKING, Union

from .utils import run, Rect

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

	@property
	def sticky(self):
		return self.data["sticky"]

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

	def set_state(self, state: "ClientState"):
		run(f"bspc node {self.id} --state {state.value}")

	def set_flag(self, flag: "NodeFlag", enable=True):
		run(f"bspc node {self.id} --flag {flag.value}={'on' if enable else 'off'}")

	def move(self, dx, dy):
		run(f'bspc node {self.id} --move {dx} {dy}')

	def resize(self, dw, dh, handle):
		run(f'bspc node {self.id} --resize {handle} {dw} {dh}')

	def set_rect(self, target: "Rect"):
		"""
		target = {'x': 2390, 'y': 1290, 'width': 800, 'height': 500}
# 		dx = target['x'] - node.client['floatingRectangle']['x']
# 		dy = target['y'] - node.client['floatingRectangle']['y']
# 		dwidth = target['width'] - node.client['floatingRectangle']['width']
# 		dheight = target['height'] - node.client['floatingRectangle']['height']
# 		pybspc.run(f'bspc node --move {dx} {dy} --resize bottom_right {dwidth} {dheight}')
		"""
		dx = target.x - self.client.floating_rectangle.x
		dy = target.y - self.client.floating_rectangle.y
		dw = target.width - self.client.floating_rectangle.width
		dh = target.height - self.client.floating_rectangle.height
		print(self.client.floating_rectangle)
		print(dx, dy, dw, dh)
		run(f'bspc node {self.id} --move {dx} {dy} --resize bottom_right {dw} {dh}')


class NodeFlag(Enum):
	HIDDEN = "hidden"
	STICKY = "sticky"
	PRIVATE = "private"
	LOCKED = "locked"
	MARKED = "marked"


class Client:
	def __init__(self, data):
		self.data = data

	@property
	def class_name(self):
		return self.data.get("className", None)

	@property
	def instance_name(self):
		return self.data.get("instanceName", None)

	@property
	def state(self) -> "ClientState":
		return ClientState(self.data["state"])

	@property
	def tiled_rectangle(self):
		return Rect(self.data["tiledRectangle"]["x"], self.data["tiledRectangle"]["y"],
					self.data["tiledRectangle"]["width"], self.data["tiledRectangle"]["height"])

	@property
	def floating_rectangle(self):
		return Rect(self.data["floatingRectangle"]["x"], self.data["floatingRectangle"]["y"],
					self.data["floatingRectangle"]["width"], self.data["floatingRectangle"]["height"])

	def __repr__(self):
		return f"<Client class: {self.class_name}>"


class ClientState(Enum):
	TILED = "tiled"
	PSEUDO_TILED = "pseudo_tiled"
	FLOATING = "floating"
	FULLSCREEN = "fullscreen"
