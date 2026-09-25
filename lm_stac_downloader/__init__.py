def classFactory(iface):
    from .plugin import LmStacDownloaderPlugin

    return LmStacDownloaderPlugin(iface)
