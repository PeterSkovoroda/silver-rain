icondir = $(datadir)/icons/hicolor

icon16dir = $(icondir)/16x16/apps
icon22dir = $(icondir)/22x22/apps
icon24dir = $(icondir)/24x24/apps
icon32dir = $(icondir)/32x32/apps
icon48dir = $(icondir)/48x48/apps
icon64dir = $(icondir)/64x64/apps
icon128dir = $(icondir)/128x128/apps
icon256dir = $(icondir)/256x256/apps

icon16_DATA = 16x16/apps/silver-rain.png
icon22_DATA = 22x22/apps/silver-rain.png
icon24_DATA = 24x24/apps/silver-rain.png
icon32_DATA = 32x32/apps/silver-rain.png
icon48_DATA = 48x48/apps/silver-rain.png
icon64_DATA = 64x64/apps/silver-rain.png
icon128_DATA = 128x128/apps/silver-rain.png
icon256_DATA = 256x256/apps/silver-rain.png

update_icon_cache = gtk-update-icon-cache -f -t $(icondir)

install-data-hook:
	$(update_icon_cache)
uninstall-hook:
	$(update_icon_cache)
