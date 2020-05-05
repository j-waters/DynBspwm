import os
from yaml import safe_load

from pybspc import Node, BSPWM, get_wm, Desktop, Monitor
from re import compile
from pathlib import Path


class Config:
	DEFAULT_LOCATION = Path(os.path.realpath(__file__)).parent.joinpath('default_config.yaml')
	CONFIG_LOCATION = os.path.join(os.getenv("HOME"), '.config/dynbsp/config.yaml')

	def __init__(self):
		with open(Config.DEFAULT_LOCATION, 'r') as f:
			self.data = safe_load(f)

		self.desktops = set()

		for desktop in self.data['desktops']:
			self.desktops.add(DesktopConfig(desktop))

		self.misc_name = self.data['misc']
		self.home_desktop = DesktopConfig(self.data['home'])

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

	def get_home(self, wm: BSPWM = None):
		if wm is None:
			wm = get_wm()

		for desktop in wm.desktops:
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

	def match(self, desktop: Desktop):
		if desktop.name == self.name or desktop.name == f"{self.name} {self.extra_name}":
			return self.match_applications(desktop)
		return False

	def match_applications(self, desktop: Desktop):
		for node in desktop.nodes:
			if self.match_node(node):
				return True

	def find(self, wm: BSPWM = None):
		if wm is None:
			wm = get_wm()
		for desktop in wm.desktops:
			if self.match(desktop):
				return desktop
		return None

	def create(self, wm: BSPWM = None):
		if wm is None:
			wm = get_wm()

		desktop = wm.current_monitor.create_desktop(self.name)
		return desktop

	def expand(self, wm: BSPWM = None, desktop: Desktop = None):
		if desktop is None:
			desktop = self.find(wm)
		if desktop:
			desktop.rename(f"{self.name} {self.extra_name}")

	def collapse(self, wm: BSPWM = None, desktop: Desktop = None):
		if desktop is None:
			desktop = self.find(wm)
		if desktop:
			desktop.rename(f"{self.name}")

	def rename(self, desktop: Desktop):
		if desktop.name != self.name:
			desktop.rename(f"{self.name}")


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
