import os

from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options as FirefoxOptions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GROUPS_JSON_PATH = os.path.join(BASE_DIR, "data","groups.json")
LINKS_JSON_PATH = os.path.join(BASE_DIR, 'data', 'links.json')
SETTINGS_USER_JSON_PATH = os.path.join(BASE_DIR, 'data', 'user.json')

firefox_paths = [
    r'C:\Program Files (x86)\Mozilla Firefox',
    r'C:\Program Files\Mozilla Firefox'
]

firefox_binary = r''

for path in firefox_paths:
    if os.path.exists(path):
        firefox_binary = path

if firefox_binary:
    firefox_binary += r'\firefox.exe'


firefox_options = FirefoxOptions()
firefox_options.set_preference("network.protocol-handler.external.zoommtg", True)
firefox_options.set_preference("network.protocol-handler.expose.zoommtg", True)
firefox_options.set_preference("network.protocol-handler.warn-external.zoommtg", False)
firefox_options.binary_location = firefox_binary

profile = FirefoxProfile()
profile.set_preference("permissions.default.microphone", 1)
profile.set_preference("permissions.default.camera", 1)

profile.set_preference("browser.link.open_newwindow", 3)
profile.set_preference("browser.link.open_newwindow.restriction", 0)

profile.set_preference("media.navigator.permission.disabled", True)
profile.set_preference("media.navigator.streams.fake", False)

firefox_options.profile = profile
