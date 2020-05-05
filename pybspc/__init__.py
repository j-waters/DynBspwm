from .desktop import Desktop
from .monitor import Monitor
from .node import Node
from .subscription import Subscriber
from .utils import run
from .bspwm import BSPWM


def get_wm():
	return BSPWM.get()


def new_subscriber():
	return Subscriber()
