import os, xbmc
from xbmcswift2 import Plugin
from kodipopcorntime.caching import CACHE_DIR

BASE_URL = "http://www.yifysubtitles.com"
API_BASE_URL = "http://api.yifysubtitles.com/subs"
HEADERS = {
    "Referer": API_BASE_URL,
}
SUBLANG_EN = {
    "0" : "none",
    "1" : "albanian",
    "2" : "arabic",
    "3" : "bengali",
    "4" : "brazilian-portuguese",
    "5" : "bulgarian",
    "6" : "chinese",
    "7" : "croatian",
    "8" : "czech",
    "9" : "danish",
    "10" : "dutch",
    "11" : "english",
    "12" : "farsi-persian",
    "13" : "finnish",
    "14" : "french",
    "15" : "german",
    "16" : "greek",
    "17" : "hebrew",
    "18" : "hungarian",
    "19" : "indonesian",
    "20" : "italian",
    "21" : "japanese",
    "22" : "korean",
    "23" : "lithuanian",
    "24" : "macedonian",
    "25" : "malay",
    "26" : "norwegian",
    "27" : "polish",
    "28" : "portuguese",
    "29" : "romanian",
    "30" : "russian",
    "31" : "serbian",
    "32" : "slovenian",
    "33" : "spanish",
    "34" : "swedish",
    "35" : "thai",
    "36" : "turkish",
    "37" : "urdu",
    "38" : "vietnamese",
}
SUBLANG_ISO = {
    "0" : "0",
    "1" : "sq",
    "2" : "ar",
    "3" : "bn",
    "4" : "pt-br",
    "5" : "bg",
    "6" : "zh",
    "7" : "hr",
    "8" : "cs",
    "9" : "da",
    "10" : "nl",
    "11" : "en",
    "12" : "fa",
    "13" : "fi",
    "14" : "fr",
    "15" : "de",
    "16" : "el",
    "17" : "he",
    "18" : "hu",
    "19" : "id",
    "20" : "it",
    "21" : "ja",
    "22" : "ko",
    "23" : "lt",
    "24" : "mk",
    "25" : "ms",
    "26" : "no",
    "27" : "pl",
    "28" : "pt",
    "29" : "ro",
    "30" : "ru",
    "31" : "sr",
    "32" : "sl",
    "33" : "es",
    "34" : "sv",
    "35" : "th",
    "36" : "tr",
    "37" : "ur",
    "38" : "vi",
}

SUBTYPES = ['.srt']

def get_lang(sub_lang_id):
    return [ SUBLANG_EN[sub_lang_id], SUBLANG_ISO[sub_lang_id] ]

SUBLANG_EN_1, SUBLANG_ISO_1 = get_lang(Plugin.get_setting("sub_language1"))
SUBLANG_EN_2, SUBLANG_ISO_2 = get_lang(Plugin.get_setting("sub_language2"))
SUBLANG_EN_3, SUBLANG_ISO_3 = get_lang(Plugin.get_setting("sub_language3"))

def get_sub_items(imdb_id):
    if SUBLANG_EN_1 == 'none':
        return None

    import urllib2
    from kodipopcorntime.utils import url_get_json
    try:
        data = url_get_json("%s/%s" % (API_BASE_URL, imdb_id), headers=HEADERS) or {}
    except urllib2.HTTPError:
        return None

    if data["subtitles"] == 0:
        return None

    data = data["subs"][imdb_id]
    if data.has_key(SUBLANG_EN_1):
        sub = "%s%s" % (BASE_URL, data[SUBLANG_EN_1][0]["url"])
        sublang = SUBLANG_ISO_1
    elif data.has_key(SUBLANG_EN_2):
        sub = "%s%s" % (BASE_URL, data[SUBLANG_EN_2][0]["url"])
        sublang = SUBLANG_ISO_2
    elif data.has_key(SUBLANG_EN_3):
        sub = "%s%s" % (BASE_URL, data[SUBLANG_EN_3][0]["url"])
        sublang = SUBLANG_ISO_3
    else:
        return None

    return [
        sub,
        sublang,
    ]

def get_subtitle(url):
    if url == '' or not type(url) is str:
        return None

    import urllib
    import zipfile
    name = os.path.join(CACHE_DIR, 'temp.zip')
    try:
        name, hdrs = urllib.urlretrieve(url, name)
        z = zipfile.ZipFile(name)
    except IOError, e:
        return None
    except zipfile.error, e:
        return None

    for each in z.namelist():
        if os.path.splitext(each)[1] in SUBTYPES:
            z.extract(each, CACHE_DIR)
            break
    z.close()
    os.unlink(name)
    return os.path.join(CACHE_DIR, each)

def clear_subtitle(file):
    if file == '' or not type(file) is str:
        return
    name = os.path.basename(file)
    if os.path.splitext(name)[1] in SUBTYPES:
        os.unlink(os.path.join(CACHE_DIR, name))
