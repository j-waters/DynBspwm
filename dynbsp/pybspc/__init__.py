from .bspwm import BSPWM
from .desktop import Desktop
from .monitor import Monitor
from .node import Node
from .subscription import Subscriber
from .utils import run


def get_wm():
	return BSPWM.get()


def new_subscriber():
	return Subscriber()
