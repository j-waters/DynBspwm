import os
from pathlib import Path
from re import compile
from shutil import copyfile
from typing import Set

from yaml import safe_load

from .pybspc import Node, BSPWM, get_wm, Desktop, Monitor


class Config:
	_home_desktop: "DesktopConfig"
	_misc_name: str
	_desktops: Set["DesktopConfig"]
	last_modified: float = None
	DEFAULT_LOCATION = Path(os.path.realpath(__file__)).parent.joinpath('default_config.yaml')
	CONFIG_LOCATION = os.path.join(os.getenv("HOME"), '.config/dynbsp/config.yaml')

	def __init__(self):
		if not os.path.exists(self.CONFIG_LOCATION):
			copyfile(self.DEFAULT_LOCATION, self.CONFIG_LOCATION)

	def load_data(self):
		if os.path.getmtime(Config.CONFIG_LOCATION) != self.last_modified:
			with open(Config.CONFIG_LOCATION, 'r') as f:
				data = safe_load(f)
			self.last_modified = os.path.getmtime(Config.CONFIG_LOCATION)

			self._desktops = set(DesktopConfig(desktop) for desktop in data['desktops'])
			self._misc_name = data['misc']
			self._home_desktop = DesktopConfig(data['home'])

	@property
	def desktops(self):
		self.load_data()
		return self._desktops

	@property
	def misc_name(self):
		self.load_data()
		return self._misc_name

	@property
	def home_desktop(self):
		self.load_data()
		return self._home_desktop

	def match_node(self, node: Node):
		for desktop in self.desktops:
			app = desktop.match_node(node)
			if app is not None:
				return app

	def match_desktop(self, desktop: Desktop):
		for desk in self.desktops:
			if desk.match(desktop):
				return desk
		return None

	def match_desktop_by_applications(self, desktop: Desktop):
		for desk in self.desktops:
			if desk.match_applications(desktop):
				return desk
		return None

	def match_home(self, desktop: Desktop):
		return self.home_desktop.name == desktop.name

	def get_desktops(self, wm: BSPWM = None, monitor: Monitor = None):
		if wm is None:
			wm = get_wm()

		for desktop in self.desktops:
			desk = desktop.find(wm)
			if desk is not None and (monitor is None or desk.monitor == monitor):
				yield desktop

	def get_home(self, monitor: Monitor):
		for desktop in monitor.desktops:
			if self.match_home(desktop):
				return desktop
		return None


class DesktopConfig:
	def __init__(self, config):
		self.name = config['name']
		self.extra_name = config.get('extra_name', None)
		self.order = config.get('order', 9999)
		self.applications = set()
		for application in config['applications']:
			self.applications.add(ApplicationConfig(application, self))

	def __repr__(self):
		return f"<DynDesktop name: {self.name} extra: {self.extra_name} order: {self.order}>"

	def match_node(self, node: Node):
		for application in self.applications:
			if application.match(node):
				return application
		return None

	def match(self, desktop: Desktop, exclude_nodes: Set[Node] = None):
		if desktop.name == self.collapsed_name or desktop.name == self.expanded_name:
			return self.match_applications(desktop, exclude_nodes)
		return False

	def match_applications(self, desktop: Desktop, exclude_nodes: Set[Node] = None):
		for node in desktop.nodes.difference(exclude_nodes if exclude_nodes is not None else set()):
			if self.match_node(node):
				return True
		return False

	def find(self, wm: BSPWM = None, exclude_nodes: Set[Node] = None):
		if wm is None:
			wm = get_wm()
		for desktop in wm.desktops:
			if self.match(desktop, exclude_nodes):
				return desktop
		return None

	def create(self, monitor: Monitor):
		if len(set(self.get_duplicates(monitor))) == 0:
			name = self.collapsed_name
		else:
			name = self.expanded_name

		desktop = monitor.create_desktop(name)
		return desktop

	def get_duplicates(self, monitor: Monitor = None, wm: BSPWM = None):
		desktops = CONFIG.get_desktops(wm, monitor)
		for desk in desktops:
			if self.name == desk.name and self != desk:
				yield desk

	@property
	def expanded_name(self):
		return f"{self.name} {self.extra_name}"

	@property
	def collapsed_name(self):
		return f"{self.name}"

	def update_name(self, desktop: Desktop = None, propagate: bool = True, wm: BSPWM = None):
		if wm is None:
			wm = get_wm()

		if desktop is None:
			desktop = self.find(wm)

		duplicates = set(self.get_duplicates(None, wm))
		if not duplicates:
			desktop.rename(self.collapsed_name)
		else:
			desktop.rename(self.expanded_name)
			if propagate:
				for desk in duplicates:
					desk.update_name(propagate=False)


class ApplicationConfig:
	def __init__(self, config, desktop: DesktopConfig):
		self.class_name = compile(config.get("class", ".*"))
		self.instance_name = compile(config.get("instance", ".*"))
		self.desktop = desktop

	def match(self, node: Node):
		if node.client is None:
			return False
		return self.class_name.match(node.client.class_name) and self.instance_name.match(node.client.instance_name)

	def __repr__(self):
		return f"<ApplicationConfig class: {self.class_name.pattern}, instance: {self.instance_name.pattern}>"


CONFIG = Config()
