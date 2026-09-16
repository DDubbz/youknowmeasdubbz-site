import asyncio
import base64
import json
import urllib.request
from datetime import date
from pathlib import Path

import websockets

CDP_LIST = "http://127.0.0.1:9223/json/list"
OUTPUT_DIR = Path(__file__).resolve().parent


async def main():
    with urllib.request.urlopen("http://localhost:4321/api/gigs.json", timeout=10) as response:
        gigs = json.load(response)
    expected_event_badges = [
        f"{date.fromisoformat(gig['date']).day} {date.fromisoformat(gig['date']).strftime('%b').upper()}"
        for gig in gigs
        if date.fromisoformat(gig["date"]) >= date.today()
    ][:4]

    with urllib.request.urlopen(CDP_LIST, timeout=10) as response:
        tabs = json.load(response)
    page = next(
        tab
        for tab in tabs
        if tab.get("url", "").startswith("http://localhost:4321")
    )

    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=None) as socket:
        request_id = 0

        async def command(method, params=None):
            nonlocal request_id
            request_id += 1
            current_id = request_id
            await socket.send(json.dumps({"id": current_id, "method": method, "params": params or {}}))
            while True:
                message = json.loads(await socket.recv())
                if message.get("id") == current_id:
                    if "error" in message:
                        raise RuntimeError(message["error"])
                    return message.get("result", {})

        async def evaluate(expression):
            result = await command(
                "Runtime.evaluate",
                {"expression": expression, "returnByValue": True, "awaitPromise": True},
            )
            if result.get("exceptionDetails"):
                raise RuntimeError(result["exceptionDetails"].get("text", "JavaScript evaluation failed"))
            return result["result"].get("value")

        await command("Page.enable")
        await command("Runtime.enable")
        await command(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    window.__homepageErrors = [];
                    window.addEventListener('error', event => {
                        const resource = event.target && event.target !== window
                            ? (event.target.src || event.target.href || event.target.tagName)
                            : '';
                        window.__homepageErrors.push(resource || event.message || 'Unknown page error');
                    }, true);
                    window.addEventListener('unhandledrejection', event => {
                        window.__homepageErrors.push(String(event.reason || 'Unhandled promise rejection'));
                    });
                """
            },
        )

        reports = []
        expected_columns = {"desktop": 4, "tablet": 2, "mobile": 1}
        for label, width, height in (
            ("desktop", 1440, 1000),
            ("tablet", 800, 900),
            ("mobile", 390, 844),
        ):
            await command(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False},
            )
            await command("Page.reload", {"ignoreCache": True})
            await asyncio.sleep(2)
            # Debug: check for JS errors and mix/gig counts
            debug = await evaluate(
                """(() => {
                    return {
                        errors: window.__homepageErrors || [],
                        mixContainer: !!document.getElementById('featured-mixes'),
                        gigContainer: !!document.getElementById('upcoming-gigs'),
                        mixCards: document.querySelectorAll('#featured-mixes .mix-card').length,
                        gigCards: document.querySelectorAll('#upcoming-gigs .gig-card').length,
                    };
                })()"""
            )
            print(f"DEBUG {label}: {debug}")
            await evaluate(
                """new Promise((resolve, reject) => {
                    const started = Date.now();
                    const check = () => {
                        const mixes = document.querySelectorAll('#featured-mixes .mix-card').length;
                        const gigs = document.querySelectorAll('#upcoming-gigs .gig-card').length;
                        if (mixes === 4 && gigs === 4) return resolve(true);
                        if (Date.now() - started > 8000) return reject(new Error(`Timed out: mixes=${mixes}, gigs=${gigs}`));
                        setTimeout(check, 100);
                    };
                    check();
                })"""
            )
            await evaluate("document.getElementById('featured-mixes').scrollIntoView({block:'center'})")
            await evaluate(
                """new Promise((resolve, reject) => {
                    const started = Date.now();
                    const check = () => {
                        const images = [...document.querySelectorAll('#featured-mixes img')];
                        if (images.length === 4 && images.every(img => img.complete && img.naturalWidth > 0)) {
                            return resolve(true);
                        }
                        if (Date.now() - started > 8000) {
                            return reject(new Error(`Timed out loading mix covers: ${images.map(img => img.naturalWidth).join(',')}`));
                        }
                        setTimeout(check, 100);
                    };
                    check();
                })"""
            )

            report = await evaluate(
                """(() => {
                    const grid = document.querySelector('#featured-mixes');
                    const firstMix = grid.querySelector('.mix-card');
                    const firstTag = grid.querySelector('.mix-card-tag');
                    const firstGig = document.querySelector('#upcoming-gigs .gig-card');
                    const template = getComputedStyle(grid).gridTemplateColumns;
                    return {
                        viewportWidth: innerWidth,
                        scrollWidth: document.documentElement.scrollWidth,
                        mixCount: grid.querySelectorAll('.mix-card').length,
                        eventCount: document.querySelectorAll('#upcoming-gigs .gig-card').length,
                        gridTemplateColumns: template,
                        columnCount: template.split(' ').filter(Boolean).length,
                        mixBorderWidth: getComputedStyle(firstMix).borderTopWidth,
                        tagBorderWidth: getComputedStyle(firstTag).borderTopWidth,
                        gigDisplay: getComputedStyle(firstGig).display,
                        gigGridColumns: getComputedStyle(firstGig).gridTemplateColumns,
                        gigBorderWidth: getComputedStyle(firstGig).borderTopWidth,
                        imageWidths: [...grid.querySelectorAll('img')].map(img => img.naturalWidth),
                        mixTitles: [...grid.querySelectorAll('.mix-card-title')].map(el => el.textContent.trim()),
                        eventTitles: [...document.querySelectorAll('#upcoming-gigs .gig-info h3')].map(el => el.textContent.trim()),
                        eventBadges: [...document.querySelectorAll('#upcoming-gigs .gig-card')].map(card =>
                            `${card.querySelector('.gig-day').textContent.trim()} ${card.querySelector('.gig-month').textContent.trim()}`
                        ),
                        pageErrors: window.__homepageErrors || []
                    };
                })()"""
            )
            report["label"] = label
            reports.append(report)

            if label in ("desktop", "mobile"):
                for section_id, section_name in (
                    ("featured-mixes", "mixes"),
                    ("upcoming-gigs", "events"),
                ):
                    await evaluate(f"document.getElementById('{section_id}').scrollIntoView({{block:'center'}})")
                    await asyncio.sleep(0.3)
                    shot = await command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
                    (OUTPUT_DIR / f"home-four-{section_name}-{label}.png").write_bytes(
                        base64.b64decode(shot["data"])
                    )

        print(json.dumps(reports, indent=2))

        failures = []
        for report in reports:
            label = report["label"]
            if report["mixCount"] != 4:
                failures.append(f"{label}: expected 4 mixes, got {report['mixCount']}")
            if report["eventCount"] != 4:
                failures.append(f"{label}: expected 4 events, got {report['eventCount']}")
            if report["eventBadges"] != expected_event_badges:
                failures.append(
                    f"{label}: event dates {report['eventBadges']} do not match {expected_event_badges}"
                )
            if report["columnCount"] != expected_columns[label]:
                failures.append(
                    f"{label}: expected {expected_columns[label]} mix columns, got {report['columnCount']}"
                )
            if report["scrollWidth"] > report["viewportWidth"]:
                failures.append(
                    f"{label}: horizontal overflow {report['scrollWidth']}px > {report['viewportWidth']}px"
                )
            if report["mixBorderWidth"] == "0px" or report["tagBorderWidth"] == "0px":
                failures.append(f"{label}: dynamic mix-card styles are not applied")
            if report["gigDisplay"] != "grid" or report["gigBorderWidth"] == "0px":
                failures.append(f"{label}: dynamic event-card styles are not applied")
            if any(width <= 0 for width in report["imageWidths"]):
                failures.append(f"{label}: one or more mix covers failed to decode")
            if report["pageErrors"]:
                failures.append(f"{label}: page errors: {report['pageErrors']}")
        if failures:
            raise AssertionError("\n".join(failures))


if __name__ == "__main__":
    asyncio.run(main())