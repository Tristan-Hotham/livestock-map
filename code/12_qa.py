"""QA: open index.html with Playwright at 1280 px and 390 px, record console errors, click the map, switch animals and
views, and save screenshots to qa/. Leaflet is served from a local copy and map tiles are blocked (the build machine has
no internet). Run: python3 code/12_qa.py"""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA = os.path.join(ROOT, "qa"); os.makedirs(QA, exist_ok=True)
LEAF = "/home/claude/rocks/npm/node_modules/leaflet/dist/"
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
errors = []


def route(r):
    u = r.request.url
    if "leaflet.min.js" in u:
        return r.fulfill(path=LEAF + "leaflet.js", content_type="application/javascript")
    if "leaflet.min.css" in u:
        return r.fulfill(path=LEAF + "leaflet.css", content_type="text/css")
    if u.startswith("http://127.0.0.1"):
        return r.continue_()
    return r.abort()


with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h, mobile in (("desktop", 1280, 900, False), ("phone", 390, 844, True)):
        pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile, device_scale_factor=2 if mobile else 1)
        pg.on("console", lambda m, n=name: m.type == "error" and "ERR_FAILED" not in m.text and errors.append((n, m.text)))
        pg.on("pageerror", lambda e, n=name: errors.append((n, str(e))))
        pg.route("**/*", route)
        pg.goto(f"http://127.0.0.1:{PORT}/index.html")
        pg.wait_for_timeout(4000)
        pg.screenshot(path=f"{QA}/{name}_top.png")
        pg.locator("#atlas").scroll_into_view_if_needed()
        pg.wait_for_timeout(500)
        box = pg.locator("#map").bounding_box()
        pg.mouse.click(box["x"] + box["width"] * .53, box["y"] + box["height"] * .38)
        pg.wait_for_timeout(1500)
        pg.locator("#atlas").screenshot(path=f"{QA}/{name}_map_main.png")
        pg.click("#spTabs .btn[data-k=sheep]")
        pg.wait_for_timeout(3000)
        pg.click("#focusRow .btn:has-text('Britain and Ireland')")
        pg.wait_for_timeout(2500)
        pg.locator("#atlas").scroll_into_view_if_needed()
        pg.evaluate("map.fire('click', { latlng: L.latLng(52.35, -3.45) })")   # mid Wales
        pg.wait_for_timeout(3000)
        pg.locator("#atlas").screenshot(path=f"{QA}/{name}_map_uk_sheep.png")
        pg.click("#viewRow .btn[data-v=pp]")
        pg.click("#spTabs .btn[data-k=cattle]")
        pg.fill("#q", "Urug")
        pg.wait_for_timeout(300)
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(2500)
        pg.locator("#atlas").screenshot(path=f"{QA}/{name}_map_country.png")
        pg.locator("#growth").scroll_into_view_if_needed(); pg.wait_for_timeout(800)
        pg.screenshot(path=f"{QA}/{name}_growth.png")
        pg.locator("#ukSheep").scroll_into_view_if_needed(); pg.wait_for_timeout(500)
        pg.screenshot(path=f"{QA}/{name}_uk.png")
        sw = pg.evaluate("document.documentElement.scrollWidth")
        print(name, "scrollWidth", sw, "fullscreen buttons", pg.locator(".mfs-btn").count())
        pg.close()
    b.close()
srv.shutdown()
print("console errors:", errors or "none")
sys.exit(1 if errors else 0)
