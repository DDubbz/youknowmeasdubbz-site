#!/usr/bin/env python3
"""Real-browser regression for /contact page."""

import asyncio
import base64
import json
import sys
import urllib.request
from pathlib import Path

import websockets

CDP_LIST = "http://127.0.0.1:9223/json/list"
PAGE_URL = "http://localhost:4321/contact"
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
                        contactMethods: document.querySelectorAll('.contact-method').length,
                        formFields: document.querySelectorAll('#booking-form input, #booking-form select, #booking-form textarea').length,
                        faqItems: document.querySelectorAll('.faq-item').length,
                        submitBtn: document.querySelector('#booking-form button[type="submit"]'),
                    };
                })()""",
                "returnByValue": True,
            })
            report = report.get("result", {}).get("value", {})
            report["label"] = label
            reports.append(report)

            shot = await call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
            path = OUT_DIR / f"contact CDP-{label}.png"
            path.write_bytes(base64.b64decode(shot["data"]))
            report["screenshot"] = str(path)

            if report["scrollWidth"] != width:
                failures.append(f"{label}: horizontal overflow {report['scrollWidth']} > {width}")
            if report["contactMethods"] != 3:
                failures.append(f"{label}: expected 3 contact methods, got {report['contactMethods']}")
            if report["formFields"] < 10:
                failures.append(f"{label}: expected at least 10 form fields, got {report['formFields']}")
            if report["faqItems"] != 8:
                failures.append(f"{label}: expected 8 FAQ items, got {report['faqItems']}")
            if report.get("submitBtn") is None:
                failures.append(f"{label}: submit button not found")
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