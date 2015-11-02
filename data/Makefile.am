SUBDIRS = icons

desktopdir = $(datadir)/applications
desktop_DATA = silver-rain.desktop

update_desktop = update-desktop-database $(desktopdir)

install-data-hook:
	$(update_desktop)
uninstall-hook:
	$(update_desktop)
