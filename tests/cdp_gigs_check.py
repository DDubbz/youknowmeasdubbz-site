#!/usr/bin/env python3
"""Real-browser regression for /gigs."""

import asyncio
import base64
import json
import sys
import urllib.request
from pathlib import Path

import websockets

CDP_LIST = "http://127.0.0.1:9223/json/list"
PAGE_URL = "http://localhost:4321/gigs"
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

        async def evaluate(expression):
            result = await call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
            return result.get("result", {}).get("value")

        await call("Page.enable")
        await call("Runtime.enable")

        reports = []
        failures = []
        viewports = (
            ("desktop", 1440, 1000, False),
            ("tablet", 800, 1000, False),
            ("mobile", 390, 844, True),
        )

        for label, width, height, mobile in viewports:
            await call("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile})
            await call("Page.navigate", {"url": PAGE_URL})
            await asyncio.sleep(1.5)

            # Wait for gigs to render
            await evaluate(
                """new Promise((resolve, reject) => {
                    const started = Date.now();
                    const poll = () => {
                        const cards = document.querySelectorAll('.gig-card').length;
                        if (cards > 0) return resolve(true);
                        if (Date.now() - started > 8000) return reject(new Error(`no gig cards after ${Date.now() - started}ms`));
                        setTimeout(poll, 100);
                    };
                    poll();
                })"""
            )

            report = await evaluate(
                """(() => {
                    const cards = [...document.querySelectorAll('.gig-card')];
                    const filters = document.querySelectorAll('#gig-filters .filter-btn');
                    const residencies = document.querySelectorAll('.residency-card');
                    const statusBadges = [...document.querySelectorAll('.gig-status')];
                    return {
                        viewportWidth: innerWidth,
                        scrollWidth: document.documentElement.scrollWidth,
                        cardCount: cards.length,
                        cardWidths: cards.slice(0, 3).map(c => c.getBoundingClientRect().width),
                        filterCount: filters.length,
                        filterBarScrollable: document.getElementById('gig-filters').scrollWidth > document.getElementById('gig-filters').clientWidth,
                        filterWrap: getComputedStyle(document.getElementById('gig-filters')).flexWrap,
                        residencyCount: residencies.length,
                        residencyColumns: getComputedStyle(document.querySelector('.residencies-grid')).gridTemplateColumns,
                        statusBadges: statusBadges.map(b => ({text: b.textContent, classes: b.className})),
                        firstCardTitle: cards[0]?.querySelector('h3')?.textContent || '',
                        firstCardStatus: statusBadges[0]?.textContent || '',
                        noUpcomingTitle: document.querySelector('.gig-info h3')?.textContent || '',
                    };
                })()"""
            )
            report["label"] = label
            reports.append(report)

            # Screenshot
            shot = await call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
            path = OUT_DIR / f"gigs-verified-{label}.png"
            path.write_bytes(base64.b64decode(shot["data"]))
            report["screenshot"] = str(path)

        for r in reports:
            label = r["label"]
            if r["scrollWidth"] != r["viewportWidth"]:
                failures.append(f"{label}: horizontal overflow {r['scrollWidth']} > {r['viewportWidth']}")
            if r["cardCount"] < 3:
                failures.append(f"{label}: only {r['cardCount']} gig cards rendered")
            if r["filterCount"] != 4:
                failures.append(f"{label}: expected 4 filters, got {r['filterCount']}")
            if r["residencyCount"] != 2:
                failures.append(f"{label}: expected 2 residency cards, got {r['residencyCount']}")
            if any(v > r["viewportWidth"] + 0.5 for v in r["cardWidths"]):
                failures.append(f"{label}: gig card wider than viewport: {r['cardWidths']}")

        print(json.dumps({"viewports": reports}, indent=2))
        if failures:
            print("FAILURES:", file=sys.stderr)
            for f in failures:
                print(f"- {f}", file=sys.stderr)
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
