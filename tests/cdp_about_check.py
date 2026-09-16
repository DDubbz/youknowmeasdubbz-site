#!/usr/bin/env python3
"""Real-browser regression for /about page."""

import asyncio
import base64
import json
import sys
import urllib.request
from pathlib import Path

import websockets

CDP_LIST = "http://127.0.0.1:9223/json/list"
PAGE_URL = "http://localhost:4321/about"
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
                    return {
                        viewportWidth: innerWidth,
                        scrollWidth: document.documentElement.scrollWidth,
                        heroPadding: getComputedStyle(document.querySelector('.section-hero')).padding,
                        heroBg: getComputedStyle(document.querySelector('.section-hero')).backgroundImage,
                        heroBgColor: getComputedStyle(document.querySelector('.section-hero')).backgroundColor,
                        approachCards: document.querySelectorAll('.approach-card').length,
                        highlightCards: document.querySelectorAll('.highlight-card').length,
                        rosterColumns: document.querySelectorAll('.roster-column').length,
                        ctaButtons: document.querySelectorAll('.cta-actions a').length,
                    };
                })()""",
                "returnByValue": True,
            })
            report = report.get("result", {}).get("value", {})
            report["label"] = label
            reports.append(report)

            shot = await call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
            path = OUT_DIR / f"about CDP-{label}.png"
            path.write_bytes(base64.b64decode(shot["data"]))
            report["screenshot"] = str(path)

            if report["scrollWidth"] != width:
                failures.append(f"{label}: horizontal overflow {report['scrollWidth']} > {width}")
            if report["approachCards"] != 3:
                failures.append(f"{label}: expected 3 approach cards, got {report['approachCards']}")
            if report["highlightCards"] != 4:
                failures.append(f"{label}: expected 4 highlight cards, got {report['highlightCards']}")
            if report["rosterColumns"] != 3:
                failures.append(f"{label}: expected 3 roster columns, got {report['rosterColumns']}")
            if report["ctaButtons"] != 2:
                failures.append(f"{label}: expected 2 CTA buttons, got {report['ctaButtons']}")
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