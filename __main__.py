from sys import argv

from helpers import new_misc_desktop

if __name__ == '__main__':
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
			new_misc_desktop(len(argv) > 2 and argv[2] == "move")

	else:
		refresh(1)

		sub.listen()
