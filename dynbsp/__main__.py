import click

from .dynbsp import sub
from .helpers import create_home, clear_empty_desktops, rename_all, update_names, reorder, remove_old_monitors, \
 new_misc_desktop, picture_in_picture
from .pybspc import get_wm
from .singleton import instance_already_running


@click.group("dynbsp", invoke_without_command=True)
@click.option('--profile', default=False, is_flag=True, help='profile application')
@click.pass_context
def cli(ctx, profile):
	if profile:
		import cProfile
		import atexit

		print("Profiling...")
		pr = cProfile.Profile()
		pr.enable()

		def exit():
			pr.disable()
			pr.dump_stats("profile.cprofile")
			print("Profiling completed")

		atexit.register(exit)

	if ctx.invoked_subcommand is None:
		start()


@cli.command()
def start():
	if instance_already_running():
		print("dynbsp already running")
		return
	create_home()
	clear_empty_desktops(get_wm())
	rename_all()
	update_names()
	reorder()
	sub.listen()
	print("hi")


@cli.command()
def multimonitor():
	remove_old_monitors()


@cli.command()
@click.option('--move', default=False, is_flag=True, help='move current node to desktop')
def new_desktop(move):
	new_misc_desktop(move)


@cli.command()
def pip():
	picture_in_picture()


if __name__ == '__main__':
	cli()
