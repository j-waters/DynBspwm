#!/usr/bin/env python
import sys
import logging

import pybspc
from json import load
import os
from sys import exit, argv
import re
from threading import Thread
from time import sleep

from datetime import datetime

logging.basicConfig(filename='dynbspwm.log',
					format='%(asctime)s | %(filename)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s',
					level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

with open(os.getenv("HOME") + '/.config/dynbsp/config.json', 'r') as f:
	CONFIG = load(f)

sub = pybspc.Subscriber()

SIDCHAR = '\ufeff'


class DeskConf:
	def __init__(self, index):
		config = CONFIG['desktops'][index]
		self.id = index + 1
		self.icon = config['icon']
		self.extra = config['extra']
		self.order = config['order']
		self.classes = config['classes']

	def __repr__(self):
		return "<DynDesktop icon: '{}' extra: '{}' id: {} order: {}>".format(self.icon, self.extra, self.id, self.order)

	def get_sid(self):
		return self.id * SIDCHAR

	def get_desktop(self):
		all = pybspc.get_desktops()
		for desktop in all:
			if desktop.name.count(SIDCHAR) == self.id:
				return desktop
		return None

	def create(self):
		if self.get_desktop() is None:
			pybspc.add_desktop(self.icon + self.get_sid())
		return self.get_desktop()

	def expand(self):
		self.get_desktop().rename(self.icon + '\S' + self.extra + self.get_sid())

	def collapse(self):
		self.get_desktop().rename(self.icon + self.get_sid())


deskConfigurations = [DeskConf(i) for i in range(len(CONFIG['desktops']))]


def getDesktopConfig(selector):
	if type(selector) == pybspc.Node:
		for desktop in deskConfigurations:
			if any(re.compile(regex).match(selector.className) for regex in
				   desktop.classes):  # selector.className in desktop.classes:
				return desktop
	if type(selector) == pybspc.Desktop:
		for desktop in deskConfigurations:
			if selector == desktop.get_desktop():
				return desktop
	return None


# TODO: fix crash, fix new chrome windows (and similar) going to new desktops, use instanceName to differentiate between things (like chrome windows)
#	   Also fix chrome not reordering properly? idk
# Give each singular desktop a predefined number of invisible characters
# If a node is created on the correct desktop, don't reorder it
@sub.event('node_add')
def node_added(node, desktop):
	conf = getDesktopConfig(node)
	if conf is not None:
		if conf != getDesktopConfig(desktop):
			desk = conf.create()
			node.to_desktop(desk)
	elif node.className in CONFIG['home']['classes']:
		node.to_desktop(pybspc.Desktop(CONFIG['home']['icon']))
	elif desktop.name == CONFIG['home']['icon']:
		desk = pybspc.add_desktop(CONFIG['misc'])
		node.to_desktop(desk)

	refresh()


def get_duplicates():
	seen = []
	duplicates = []
	alive = []
	for desktop in deskConfigurations:
		if desktop.get_desktop() is not None:
			alive.append(desktop)
			if desktop.icon in seen:
				duplicates.append(desktop.icon)
			seen.append(desktop.icon)

	return [desktop for desktop in alive if desktop.icon in duplicates]


def expand_duplicates():
	for desktop in get_duplicates():
		desktop.expand()


def collapse_duplicates():
	duplicates = get_duplicates()
	for desktop in deskConfigurations:
		if desktop.get_desktop() is not None and desktop not in duplicates:
			desktop.collapse()


@sub.event('node_remove')
def node_removed(desktop):
	if desktop.name != CONFIG['home']['icon']:
		if len(desktop.get_nodes()) == 0:
			desktop.remove()

	refresh()


@sub.event('node_transfer')
def desktop_transfer():
	refresh()


def cleanup():
	for monitor in pybspc.get_monitors():
		firsthome = False
		for desktop in monitor.get_desktops():
			if desktop.name != CONFIG['home']['icon'] or firsthome:
				if len(desktop.get_nodes()) == 0:
					desktop.remove()
			if desktop.name == CONFIG['home']['icon']:
				firsthome = True


def reorder():
	desktops = list(deskConfigurations)
	desktops.sort(key=lambda d: d.order)

	desktops = [desktop.get_desktop() for desktop in desktops if desktop.get_desktop() is not None]
	desktops.insert(0, pybspc.Desktop(''))
	desktops.extend([desk for desk in pybspc.get_desktops() if desk.name not in [desk2.name for desk2 in desktops]])

	print(desktops)

	pybspc.reorder(desktops)


def refresh(level=1):
	"""
	level 1: expand/collapse, reorder
	level 2: + cleanup
	"""
	if level <= 2:
		cleanup()
	if level <= 1:
		expand_duplicates()
		collapse_duplicates()
		reorder()


def pip():
	node = pybspc.Node('focused')
	if node.sticky and node.client['state'] == 'floating':
		pybspc.run('bspc node --state tiled --flag sticky=off')
	else:
		pybspc.run('bspc node --state floating --flag sticky=on')
		node.query()
		target = {'x': 2390, 'y': 1290, 'width': 800, 'height': 500}
		dx = target['x'] - node.client['floatingRectangle']['x']
		dy = target['y'] - node.client['floatingRectangle']['y']
		dwidth = target['width'] - node.client['floatingRectangle']['width']
		dheight = target['height'] - node.client['floatingRectangle']['height']
		pybspc.run(f'bspc node --move {dx} {dy} --resize bottom_right {dwidth} {dheight}')


def screensaver():
	"""
	1. run st -e pipes
	2. make fullscreen:
		bspc node <node> --state fullscreen
	3. run pipes??
	"""
	proc = pybspc.run(
		'gnome-terminal --hide-menubar --full-screen --profile=Screensaver --command /home/james/.scripts/pipes.sh',
		wait=False)


def screensaverChecker():
	def _checkScreensaver():
		IDLETIME = 120
		isIdle = False
		pid = None
		while True:
			idle = int(pybspc.run('xprintidle').stdout.read().decode('utf-8')) / 1000
			node = pybspc.Node('focused')
			if idle > IDLETIME and not isIdle and node.client['state'] != 'fullscreen':
				isIdle = True
				pid = screensaver()
			if idle < IDLETIME:
				isIdle = False
				if pid != None:
					o = pybspc.run('pkill {}'.format(pid))
					pid = None
			sleep(5)

	t = Thread(target=_checkScreensaver)
	t.setDaemon(True)
	t.start()


def multimonitor(debug=True):
	# This is not controlled by config yet, it's hardcoded
	proc = pybspc.run('xrandr')
	xrandr = proc.stdout.read().strip().decode('utf-8')
	external = pybspc.Monitor('HDMI1')
	laptop = pybspc.Monitor('eDP1')
	if "HDMI1 connected" in xrandr and debug:
		if not external.exists():
			external.create("1920x1080+0+0")
		laptop.move_all(external, leftover='', exclude=[''])
		if '' not in [desk.name for desk in external.get_desktops()]:
			external.add_desktop('')
	elif external.exists():
		external.move_all(laptop, exclude=[''])
		external.remove()
	refresh(1)


if __name__ == "__main__":
	if len(argv) > 1:
		if argv[1] == "pip":
			pip()
		if argv[1] == "multimonitor":
			multimonitor()
		if argv[1] == "multimonitor-test":
			b = True
			while True:
				multimonitor(b)
				b = not b
				input(">")
		if argv[1] == "new":
			desk = pybspc.add_desktop(CONFIG['misc'])
			if len(argv) > 2 and argv[2] == "move":
				pybspc.run('bspc node --to-desktop {} --follow'.format(desk.selector))
	else:
		refresh(1)

		screensaverChecker()

		sub.listener()
