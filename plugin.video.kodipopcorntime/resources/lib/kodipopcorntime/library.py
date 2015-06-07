from kodipopcorntime.common import plugin

LIBRARY_PATHS = {
    "KODI Popcorn Time Movies": {
        "strContent": "movies",
        "strScraper": "metadata.themoviedb.org",
        "useFolderNames": 0,
        "strSettings": """<settings><setting id="RatingS" value="TMDb" /><setting id="TrailerQ" value="No" /><setting id="certprefix" value="Rated " /><setting id="fanart" value="true" /><setting id="keeporiginaltitle" value="false" /><setting id="language" value="en" /><setting id="tmdbcertcountry" value="us" /><setting id="trailer" value="true" /></settings>""",
        "strPath": "special://profile/addon_data/%s/movies/" % plugin.id,
    },
}

def _get_video_db():
    import xbmc
    versions = {"12": "75", "13": "77"}
    major = xbmc.getInfoLabel("System.BuildVersion").split(".")[0]
    return xbmc.translatePath("special://database/MyVideos%s.db" % versions[major])

def _rescan_library(path=None):
    import json, xbmc
    params = {}
    if path:
        params["directory"] = path
    xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "VideoLibrary.Scan",
        "params": params,
    }))

@plugin.route("/library/add")
def library_add():
    import os, xbmc, xbmcgui
    from urllib import unquote
    from kodipopcorntime.magnet import display_name

    play_url = "plugin://plugin.video.kodipopcorntime/play/"
    name = LIBRARY_PATHS.iterkeys().next()
    entry = LIBRARY_PATHS.itervalues().next()
    if not xbmcgui.Dialog().yesno("Add to %s" % name, "Add \"%s\" to %s ?" % (plugin.request.args_dict["label"], name), ""):
        return

    real_path = xbmc.translatePath(entry["strPath"])
    if not os.path.exists(real_path):
        os.makedirs(real_path)
    sub, magnet_uri = plugin.request.args_dict["href"].replace(play_url, "").split('/', 1)
    with open(os.path.join(real_path, "%s.strm" % display_name(unquote(magnet_uri))), "w") as fp:
        fp.write("%s%s/%s" % (play_url, sub, magnet_uri))
    _rescan_library(entry["strPath"])
    plugin.notify("Added to %s." % name)

@plugin.route("/library/install")
def library_install():
    import os, sqlite3, xbmc, xbmcgui
    from contextlib import closing
    import xml.etree.ElementTree as ET

    def _make_source_node(name, path):
        source = ET.Element("source")
        ET.SubElement(source, "name").text = name
        ET.SubElement(source, "path").text = path
        return source

    sources_filename = xbmc.translatePath("special://userdata/sources.xml")
    root = ET.parse(sources_filename)
    video_node = root.find("./video")
    with closing(sqlite3.connect(_get_video_db())) as conn:
        for name, entry in LIBRARY_PATHS.items():
            if not os.path.exists(xbmc.translatePath(entry["strPath"])):
                os.makedirs(xbmc.translatePath(entry["strPath"]))
            video_node.append(_make_source_node(name, entry["strPath"]))
            if not conn.execute('''SELECT idPath FROM path WHERE strPath=:strPath''', entry).fetchone():
                keys = []
                values = []
                for key, value in entry.items():
                    keys.append(key)
                    values.append(value)
                conn.execute('''INSERT INTO path(%s) VALUES (?, ?, ?, ?, ?)''' % ", ".join(keys), values)
        conn.commit()
        root.write(sources_filename)
    _rescan_library()
    xbmcgui.Dialog().ok("Installation complete.", "KODI will now quit. Please restart it.", "")
    xbmc.executebuiltin("XBMC.Quit()")

@plugin.route("/library/uninstall")
def library_uninstall():
    import sqlite3, xbmc, xbmcgui
    from contextlib import closing
    import xml.etree.ElementTree as ET
    sources_filename = xbmc.translatePath("special://userdata/sources.xml")
    root = ET.parse(sources_filename)
    video_node = root.find("./video")
    with closing(sqlite3.connect(_get_video_db())) as conn:
        for source in list(video_node.findall("source")):
            if source.find("name").text in LIBRARY_PATHS:
                video_node.remove(source)
        for content_type, entry in LIBRARY_PATHS.items():
            conn.execute('''DELETE FROM path WHERE strPath=:strPath''', entry)
        conn.commit()
        root.write(sources_filename)
    _rescan_library()
    xbmcgui.Dialog().ok("Uninstallation complete.", "KODI will now quit. Please restart it.", "")
    xbmc.executebuiltin("XBMC.Quit()")

def library_context(fn):
    """Makes sure that if the listitem doesn't have a fanart, we properly set one."""
    from functools import wraps
    @wraps(fn)
    def _fn(*a, **kwds):
        items = fn(*a, **kwds)
        if items is not None:
            for item in items:
                if item.get("is_playable"):
                    label = item["label"].encode("utf-8")
                    item.setdefault("context_menu", []).extend([
                        ("Add to Movies", "XBMC.RunPlugin(%s)" % plugin.url_for("library_add", label=label, href=item["path"])),
                    ])
                yield item
    return _fn
