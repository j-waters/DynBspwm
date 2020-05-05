from typing import Union, Set

from config import CONFIG, DesktopConfig
from pybspc import Monitor, BSPWM, get_wm, Node, Desktop


def clear_empty_desktops(container: Union[BSPWM, Monitor]):
	for desktop in container.desktops:
		if len(desktop.nodes) == 0 and not CONFIG.match_home(desktop):
			desktop.delete()


def new_misc_desktop(move=False, node: Node = None, wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	desk = wm.current_monitor.create_desktop(CONFIG.misc_name)
	if move:
		if node is None:
			node = wm.current_monitor.current_desktop.current_node
		node.to_desktop(desk, follow=True)


def _get_duplicates(desktop: DesktopConfig, desktops: Set[DesktopConfig]):
	for desk in desktops:
		if desktop.name == desk.name:
			yield desk


def expand_duplicates(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	desktops = set(CONFIG.get_desktops(wm))
	while len(desktops) > 0:
		desktop = desktops.pop()
		duplicates = set(_get_duplicates(desktop, desktops))
		for desk in duplicates:
			desktops.remove(desk)
			desktop.expand(wm)
			desk.expand(wm)


def collapse_non_duplicates(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	desktops = set(CONFIG.get_desktops(wm))
	while len(desktops) > 0:
		desktop = desktops.pop()
		duplicates = set(_get_duplicates(desktop, desktops))
		if len(duplicates) == 0:
			desktop.collapse(wm)
		else:
			desktops = desktops.difference(duplicates)


def rename_all(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	for desktop in wm.desktops:
		desk = CONFIG.match_desktop_by_applications(desktop)
		if desk is not None:
			if len(set(_get_duplicates(desktop, CONFIG.get_desktops(wm, desktop.monitor)))) == 1:
				desk.collapse(wm, desktop)
			else:
				desk.expand(wm, desktop)


def create_home(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	if CONFIG.get_home(wm) is None:
		CONFIG.home_desktop.create(wm)


def reorder(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()

	def _remove_duplicates(seq):
		seen = set()
		seen_add = seen.add
		return [x for x in seq if not (x in seen or seen_add(x))]

	for monitor in wm.monitors:
		ordered = [
			desktop.find(wm) for desktop in sorted(CONFIG.get_desktops(wm, monitor), key=lambda desktop: desktop.order)
		]
		ordered.insert(0, CONFIG.get_home(wm))
		ordered = _remove_duplicates(ordered)
		not_included = [desktop for desktop in monitor.desktops if desktop not in ordered]
		ordered = ordered + not_included
		monitor.reorder(ordered)
