from typing import Union

from .config import CONFIG
from .pybspc import Monitor, BSPWM, get_wm, Node, run, ClientState, NodeFlag, Rect


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


def rename_all(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	for desktop in wm.desktops:
		desk = CONFIG.match_desktop_by_applications(desktop)
		if desk is not None:
			desk.update_name(desktop, wm)


def update_names(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	for desktop in CONFIG.get_desktops(wm):
		desktop.update_name(wm=wm)


def create_home(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	for monitor in wm.monitors:
		if CONFIG.get_home(monitor) is None:
			# monitor.create_desktop()
			CONFIG.home_desktop.create(monitor)


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
		ordered.insert(0, CONFIG.get_home(monitor))
		ordered = _remove_duplicates(ordered)
		not_included = [desktop for desktop in monitor.desktops if desktop not in ordered]
		ordered = ordered + not_included
		monitor.reorder(ordered)


def remove_old_monitors(wm: BSPWM = None):
	if wm is None:
		wm = get_wm()
	xrandr = run('xrandr').read()
	laptop_monitor = next((monitor for monitor in wm.monitors if monitor.name == "eDP1"))
	for monitor in wm.monitors:
		if f"{monitor.name} connected" not in xrandr:
			for desktop in monitor.desktops:
				if CONFIG.match_home(desktop):
					if len(desktop.nodes) > 0:
						misc = laptop_monitor.create_desktop(CONFIG.misc_name)
						for node in desktop.nodes:
							node.to_desktop(misc)
				else:
					desktop.to_monitor(laptop_monitor)
			monitor.remove()
	reorder(wm)


def new_monitor_added(monitor: Monitor, wm: BSPWM = None):
	create_home()
	clear_empty_desktops(monitor)
	laptop_monitor = next((monitor for monitor in wm.monitors if monitor.name == "eDP1"))
	if "HDMI" in monitor.name:
		for desktop in laptop_monitor.desktops:
			if not CONFIG.match_home(desktop):
				desktop.to_monitor(monitor)
		reorder(wm)


def picture_in_picture():
	wm = get_wm()
	current_node = wm.current_monitor.current_desktop.current_node
	if current_node.sticky and current_node.client.state is ClientState.FLOATING:
		current_node.set_state(ClientState.TILED)
		current_node.set_flag(NodeFlag.STICKY, False)
	else:
		current_node.set_state(ClientState.FLOATING)
		current_node.set_flag(NodeFlag.STICKY, True)

		monitor_rect = wm.current_monitor.rectangle
		monitor_padding = wm.current_monitor.padding
		extra_padding = wm.current_monitor.window_gap - wm.current_monitor.border_width
		w = round(monitor_rect.width * 0.3)
		h = round(monitor_rect.height * 0.3)
		x = monitor_rect.x + monitor_rect.width - w - monitor_padding.right - extra_padding
		y = monitor_rect.y + monitor_rect.height - h - monitor_padding.bottom - extra_padding
		current_node.set_rect(Rect(x, y, w, h))
