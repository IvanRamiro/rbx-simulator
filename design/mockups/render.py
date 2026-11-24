"""Renders the HTML mockups in this folder to PNG with headless Google Chrome (macOS).

    python3 design/mockups/render.py            # every page below
    python3 design/mockups/render.py hud-walk   # one by name

Output goes to design/previews/. The pages use the game's own fonts and icons (fonts/ and assets/ here)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "previews")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# name: (page and query, width, height, device scale)
PAGES = {
    "hud-walk": ("hud.html", 1920, 978, 1),
    "hud-carry": ("hud.html?carry", 1920, 978, 1),
    "pets-v2": ("pets.html", 1920, 978, 1),
    "settings-v2": ("settings.html", 1920, 978, 1),
    "phone-closed": ("phone.html?closed", 685, 338, 2),
    "phone-menu": ("phone.html?menu", 685, 338, 2),
    "phone-pets": ("phone.html?pets", 685, 338, 2),
}


def render(name):
    page, w, h, scale = PAGES[name]
    path, _, query = page.partition("?")
    url = "file://" + os.path.join(HERE, path) + ("?" + query if query else "")
    out = os.path.join(OUT, name + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000",
                    f"--force-device-scale-factor={scale}", f"--window-size={w},{h}", f"--screenshot={out}", url],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n in (sys.argv[1:] or list(PAGES)):
        if os.path.exists(os.path.join(HERE, PAGES[n][0].partition("?")[0])):
            render(n)
