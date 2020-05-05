from pybspc import get_wm, new_subscriber

sub = new_subscriber()


@sub.event("node_add")
def node_add(wm, monitor, desktop, node):
	print("NODE ADDED")
	print(monitor)
	print(desktop)
	print(node)


if __name__ == "__main__":
	sub.listen()
