#!/usr/bin/env python3
"""Real-browser regression for /services page."""

import asyncio
import base64
import json
import sys
import urllib.request
from pathlib import Path

import websockets

CDP_LIST = "http://127.0.0.1:9223/json/list"
PAGE_URL = "http://localhost:4321/services"
OUT_DIR = Path(__file__).resolve().parent


async def run():
    tabs = json.load(urllib.request.urlopen(CDP_LIST, timeout=5))
    page = next((tab for tab in tabs if tab.get("type") == "page"), None)
    if not page:
        raise RuntimeError("No CDP page target found")

    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        call_id = 0

        async def call(method, params=None):
            nonlocal call_id
            call_id += 1
            request_id = call_id
            await ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
            while True:
                message = json.loads(await ws.recv())
                if message.get("id") == request_id:
                    if "error" in message:
                        raise RuntimeError(f"{method}: {message['error']}")
                    return message.get("result", {})

        await call("Page.enable")
        await call("Runtime.enable")

        reports = []
        failures = []
        viewports = (
            ("desktop", 1440, 1000),
            ("mobile", 390, 844),
        )

        for label, width, height in viewports:
            await call("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": label == "mobile"})
            await call("Page.navigate", {"url": PAGE_URL})
            await asyncio.sleep(2)

            report = await call("Runtime.evaluate", {
                "expression": """(() => {
                    // Get the source CSS text for the hero rule
                    let heroRule = '';
                    try {
                        const sheets = [...document.styleSheets];
                        outer: for (const sheet of sheets) {
                            for (const rule of sheet.cssRules) {
                                if (rule.selectorText === '.section-hero') {
                                    heroRule = rule.style.cssText;
                                    break outer;
                                }
                            }
                        }
                    } catch (e) { /* CORS */ }
                    return {
                        viewportWidth: innerWidth,
                        scrollWidth: document.documentElement.scrollWidth,
                        heroPadding: getComputedStyle(document.querySelector('.section-hero')).padding,
                        heroPaddingSource: heroRule,
                        heroBg: getComputedStyle(document.querySelector('.section-hero')).backgroundImage,
                        heroBgColor: getComputedStyle(document.querySelector('.section-hero')).backgroundColor,
                        serviceDetails: document.querySelectorAll('.service-detail').length,
                        productionItems: document.querySelectorAll('.production-item').length,
                        processSteps: document.querySelectorAll('.process-step').length,
                        areaCards: document.querySelectorAll('.area-card').length,
                        ctaButtons: document.querySelectorAll('.cta-actions a').length,
                    };
                })()""",
                "returnByValue": True,
            })
            report = report.get("result", {}).get("value", {})
            report["label"] = label
            reports.append(report)

            shot = await call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
            path = OUT_DIR / f"services CDP-{label}.png"
            path.write_bytes(base64.b64decode(shot["data"]))
            report["screenshot"] = str(path)

            if report["scrollWidth"] != width:
                failures.append(f"{label}: horizontal overflow {report['scrollWidth']} > {width}")
            if report["serviceDetails"] < 3:
                failures.append(f"{label}: only {report['serviceDetails']} service panels")
            if report["productionItems"] != 3:
                failures.append(f"{label}: expected 3 production items, got {report['productionItems']}")
            if report["processSteps"] != 7:
                failures.append(f"{label}: expected 7 process steps, got {report['processSteps']}")
            if report["areaCards"] != 3:
                failures.append(f"{label}: expected 3 area cards, got {report['areaCards']}")
            if report["ctaButtons"] != 2:
                failures.append(f"{label}: expected 2 CTA buttons, got {report['ctaButtons']}")
            # Check source CSS for clamp() in hero padding
            source = (OUT_DIR.parent / "src" / "pages" / "services.astro").read_text()
            if "clamp(" not in source:
                failures.append(f"{label}: hero padding not using clamp() in source")
            if "gradient" not in report.get("heroBg", ""):
                failures.append(f"{label}: hero background-image missing gradient: {report['heroBg']}")
            if "gradient" not in report.get("heroBgColor", "") and report.get("heroBgColor") == "rgba(0, 0, 0, 0)":
                failures.append(f"{label}: hero background-color not set: {report['heroBgColor']}")

        print(json.dumps(reports, indent=2))
        if failures:
            print("FAILURES:", file=sys.stderr)
            for f in failures:
                print(f"- {f}", file=sys.stderr)
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
