#!/usr/bin/env python3
"""Real-browser regression for the modern /mixes player."""

import asyncio
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

import websockets

CDP_LIST = "http://127.0.0.1:9223/json/list"
PAGE_URL = "http://localhost:4321/mixes"
OUT_DIR = Path(__file__).resolve().parent


async def run():
    tabs = json.load(urllib.request.urlopen(CDP_LIST, timeout=5))
    page = next((tab for tab in tabs if tab.get("type") == "page"), None)
    if not page:
        raise RuntimeError("No CDP page target found")

    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
        call_id = 0
        events = []

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
                events.append(message)

        async def evaluate(expression, await_promise=False):
            result = await call(
                "Runtime.evaluate",
                {
                    "expression": expression,
                    "returnByValue": True,
                    "awaitPromise": await_promise,
                },
            )
            return result.get("result", {}).get("value")

        async def click_selector(selector):
            await evaluate(f"document.querySelector({json.dumps(selector)}).scrollIntoView({{block:'center'}})")
            await asyncio.sleep(0.5)
            center = await evaluate(
                f"""(() => {{
                    const r = document.querySelector({json.dumps(selector)}).getBoundingClientRect();
                    return {{x:r.left+r.width/2,y:r.top+r.height/2}};
                }})()"""
            )
            hit = await evaluate(
                f"""(() => {{
                    const el = document.elementFromPoint({center['x']}, {center['y']});
                    return {{tag:el?.tagName || '', cls:el?.className?.baseVal || el?.className || '', label:el?.getAttribute?.('aria-label') || '', src:el?.currentSrc || el?.src || ''}};
                }})()"""
            )
            for event_type, button_state in (("mousePressed", 1), ("mouseReleased", 0)):
                await call(
                    "Input.dispatchMouseEvent",
                    {
                        "type": event_type,
                        "x": center["x"],
                        "y": center["y"],
                        "button": "left",
                        "buttons": button_state,
                        "clickCount": 1,
                    },
                )
            return {"center": center, "hit": hit}

        await call("Page.enable")
        await call("Runtime.enable")
        await call(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                  window.__mixesErrors = [];
                  window.addEventListener('error', event => window.__mixesErrors.push(String(event.message || event.error)));
                  window.addEventListener('unhandledrejection', event => window.__mixesErrors.push(String(event.reason)));
                """
            },
        )

        reports = []
        failures = []
        viewports = (
            ("desktop", 1440, 1000, False),
            ("tablet", 800, 1000, False),
            ("mobile", 390, 844, True),
        )

        for label, width, height, mobile in viewports:
            await call(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": mobile,
                },
            )
            await call("Page.navigate", {"url": PAGE_URL})
            await asyncio.sleep(0.8)
            await evaluate(
                """new Promise((resolve, reject) => {
                    const started = Date.now();
                    const poll = () => {
                      const count = document.querySelectorAll('.playlist-track').length;
                      const title = document.querySelector('[data-track-title]')?.textContent || '';
                      if (count === 4 && title.includes('Cultural Council')) return resolve(true);
                      if (Date.now() - started > 10000) return reject(new Error(`tracks=${count}; title=${title}`));
                      setTimeout(poll, 100);
                    };
                    poll();
                })""",
                await_promise=True,
            )
            await evaluate(
                """new Promise((resolve, reject) => {
                    const started = Date.now();
                    const poll = () => {
                      const images = [...document.querySelectorAll('.playlist-track-cover img')];
                      if (images.length === 4 && images.every(img => img.complete && img.naturalWidth > 0)) return resolve(true);
                      if (Date.now() - started > 10000) return reject(new Error(`covers=${images.map(img => img.naturalWidth).join(',')}`));
                      setTimeout(poll, 100);
                    };
                    poll();
                })""",
                await_promise=True,
            )
            await evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.2)

            # Verify the play button is actually reachable at the center point before clicking
            await evaluate(
                """(() => {
                    const btn = document.querySelector('[data-play-btn]');
                    if (!btn) return;
                    const r = btn.getBoundingClientRect();
                    btn.scrollIntoView({block: 'center'});
                })()"""
            )
            await asyncio.sleep(0.5)

            report = await evaluate(
                """(() => {
                    const rect = sel => {
                      const node = document.querySelector(sel);
                      if (!node) return null;
                      const r = node.getBoundingClientRect();
                      return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom};
                    };
                    const images = [...document.querySelectorAll('.playlist-track-cover img')];
                    return {
                      viewportWidth: innerWidth,
                      scrollWidth: document.documentElement.scrollWidth,
                      trackCount: document.querySelectorAll('.playlist-track').length,
                      player: rect('.player-main'),
                      sidebar: rect('.playlist-sidebar'),
                      play: rect('[data-play-btn]'),
                      timeline: rect('.player-timeline'),
                      equalizer: rect('.equalizer-bars'),
                      pauseToggleCount: document.querySelectorAll('[data-equalizer-toggle], .equalizer-toggle').length,
                      title: document.querySelector('[data-track-title]')?.textContent || '',
                      playlistCount: document.querySelector('[data-playlist-count]')?.textContent || '',
                      coverNaturalWidths: images.map(img => img.naturalWidth),
                      coverSources: images.map(img => img.currentSrc || img.src),
                      coverWidths: images.map(img => img.getBoundingClientRect().width),
                      currentArtwork: document.querySelector('[data-player-artwork]')?.getAttribute('src') || '',
                      audioReadyState: document.querySelector('[data-audio]')?.readyState,
                      pageErrors: window.__mixesErrors || []
                    };
                })()"""
            )
            report["label"] = label
            reports.append(report)

            if report["scrollWidth"] != width:
                failures.append(f"{label}: horizontal overflow {report['scrollWidth']} > {width}")
            if report["trackCount"] != 4:
                failures.append(f"{label}: expected 4 tracks, got {report['trackCount']}")
            if report["pauseToggleCount"] != 0:
                failures.append(f"{label}: analyzer pause control still present")
            if report["playlistCount"] != "4 mixes":
                failures.append(f"{label}: playlist count is {report['playlistCount']!r}")
            if not report["play"] or report["play"]["width"] < 40:
                failures.append(f"{label}: play control is missing or too small")
            if not report["timeline"] or not report["equalizer"]:
                failures.append(f"{label}: timeline/equalizer missing")
            if len(report["coverNaturalWidths"]) != 4 or any(v <= 0 for v in report["coverNaturalWidths"]):
                failures.append(f"{label}: one or more playlist covers failed to decode")
            if any(v > 80 for v in report["coverWidths"]):
                failures.append(f"{label}: playlist covers escaped compact layout: {report['coverWidths']}")
            if report["pageErrors"]:
                failures.append(f"{label}: page errors: {report['pageErrors']}")

            if label in ("desktop", "mobile"):
                metrics = await call("Page.getLayoutMetrics")
                content = metrics["contentSize"]
                shot = await call(
                    "Page.captureScreenshot",
                    {
                        "format": "png",
                        "captureBeyondViewport": True,
                        "clip": {
                            "x": 0,
                            "y": 0,
                            "width": content["width"],
                            "height": content["height"],
                            "scale": 1,
                        },
                    },
                )
                path = OUT_DIR / f"mixes-verified-{label}.png"
                path.write_bytes(base64.b64decode(shot["data"]))
                report["screenshot"] = str(path)

            await evaluate(
                """(() => {
                  window.__mixesPlayFailures = [];
                  const audio = document.querySelector('[data-audio]');
                  const originalPlay = audio.play.bind(audio);
                  audio.play = (...args) => originalPlay(...args).catch(error => {
                    window.__mixesPlayFailures.push(`${error.name}: ${error.message}`);
                    throw error;
                  });
                })()"""
            )
            click_result = await click_selector("[data-play-btn]")
            await asyncio.sleep(5)
            playback = await evaluate(
                """(() => {
                    const audio = document.querySelector('[data-audio]');
                    return {
                      paused: audio.paused,
                      currentTime: audio.currentTime,
                      label: document.querySelector('[data-play-btn]').getAttribute('aria-label'),
                      failures: window.__mixesPlayFailures || []
                    };
                })()"""
            )
            report["click"] = click_result
            report["playback"] = playback
            if playback["paused"] or playback["currentTime"] < 0.5 or playback["label"] != "Pause":
                failures.append(f"{label}: playback did not progress: {playback}")

        # Verify homepage deep links select the corresponding mix without requiring autoplay.
        await call("Page.navigate", {"url": PAGE_URL + "?play=avacado-saturday"})
        await asyncio.sleep(1)
        deep_link = await evaluate(
            """new Promise((resolve, reject) => {
              const started = Date.now();
              const poll = () => {
                const title = document.querySelector('[data-track-title]')?.textContent || '';
                if (title.includes('Avacado')) return resolve({
                  title,
                  artwork: document.querySelector('[data-player-artwork]')?.getAttribute('src') || '',
                  selected: document.querySelector('.playlist-track[aria-selected="true"]')?.dataset.mix || ''
                });
                if (Date.now() - started > 8000) return reject(new Error(title));
                setTimeout(poll, 100);
              };
              poll();
            })""",
            await_promise=True,
        )
        if "avacado-saturday-2024.webp" not in deep_link.get("artwork", ""):
            failures.append(f"deep-link artwork mismatch: {deep_link}")
        if deep_link.get("selected", "").removesuffix(".md") != "avacado-saturday":
            failures.append(f"deep-link selection mismatch: {deep_link}")

        print(json.dumps({"viewports": reports, "deepLink": deep_link}, indent=2))
        if failures:
            print("FAILURES:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))