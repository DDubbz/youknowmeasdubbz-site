import asyncio
import base64
import json
import urllib.request
from pathlib import Path

import websockets

CDP_LIST = "http://127.0.0.1:9223/json/list"
OUTPUT_DIR = Path(__file__).resolve().parent


async def main():
    with urllib.request.urlopen(CDP_LIST, timeout=10) as response:
        tabs = json.load(response)
    page = next(
        tab
        for tab in tabs
        if tab.get("url", "").startswith("http://localhost:4321") or tab.get("url", "").startswith("http://127.0.0.1:4321")
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

        await command("Page.navigate", {"url": "http://localhost:4321/"})
        await asyncio.sleep(2)

        reports = []
        for label, width, height in (
            ("desktop", 1440, 1000),
            ("mobile", 390, 844),
        ):
            await command(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False},
            )
            await command("Page.reload", {"ignoreCache": True})
            await asyncio.sleep(2)
            # Ensure we're at the top of the page
            await command("Runtime.evaluate", {"expression": "window.scrollTo(0, 0)"})
            await asyncio.sleep(0.5)

            before = await evaluate(
                """(() => {
                    const player = document.querySelector('[data-player]');
                    const controls = player.querySelector('[data-player-controls]');
                    const bars = controls.nextElementSibling; // equalizer-bars is a sibling
                    const play = player.querySelector('[data-play-btn]');
                    const rect = el => {
                        const r = el.getBoundingClientRect();
                        const s = getComputedStyle(el);
                        return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,
                            display:s.display,visibility:s.visibility,opacity:s.opacity,position:s.position};
                    };
                    const a = controls.getBoundingClientRect();
                    const b = bars.getBoundingClientRect();
                    const p = play.getBoundingClientRect();
                    return {
                        viewport:{innerWidth,innerHeight,scrollWidth:document.documentElement.scrollWidth},
                        player:rect(player),controls:rect(controls),bars:rect(bars),play:rect(play),
                        overlap:!(a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom),
                        barsBelowControls:b.top>=a.bottom,
                        playCenter:{x:p.left+p.width/2,y:p.top+p.height/2},
                        title:player.querySelector('[data-track-title]').textContent,
                        duration:player.querySelector('[data-duration]').textContent,
                        current:player.querySelector('[data-current-time]').textContent,
                        disabled:play.disabled,
                        ariaLabel:play.getAttribute('aria-label'),
                        audioRequest:performance.getEntriesByType('resource').some(entry => entry.name.includes('/mixes/') && entry.name.endsWith('.mp3'))
                    };
                })()"""
            )

            screenshot = await command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
            screenshot_path = OUTPUT_DIR / f"player-verified-{label}.png"
            screenshot_path.write_bytes(base64.b64decode(screenshot["data"]))

            # Use a real CDP pointer event so Chrome treats playback as user-initiated.
            await evaluate("document.querySelector('[data-player]').scrollIntoView({block: 'center'})")
            await asyncio.sleep(0.35)
            click_point = await evaluate(
                """(() => {
                    const rect = document.querySelector('[data-play-btn]').getBoundingClientRect();
                    return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
                })()"""
            )
            await command("Input.dispatchMouseEvent", {
                "type": "mousePressed", "x": click_point["x"], "y": click_point["y"],
                "button": "left", "clickCount": 1,
            })
            await command("Input.dispatchMouseEvent", {
                "type": "mouseReleased", "x": click_point["x"], "y": click_point["y"],
                "button": "left", "clickCount": 1,
            })
            await asyncio.sleep(4)

            after = await evaluate(
                """(() => {
                    const player=document.querySelector('[data-player]');
                    const button=player.querySelector('[data-play-btn]');
                    return {
                        ariaLabel:button.getAttribute('aria-label'),
                        current:player.querySelector('[data-current-time]').textContent,
                        duration:player.querySelector('[data-duration]').textContent,
                        pausedIcon:button.querySelectorAll('rect').length===2
                    };
                })()"""
            )
            reports.append({"label": label, "before": before, "afterPlay": after, "screenshot": str(screenshot_path)})

            # Pause it again for cleanup
            if after["ariaLabel"] == "Pause":
                await evaluate(
                    """(() => {
                        const btn = document.querySelector('[data-play-btn]');
                        if (btn) btn.click();
                    })()"""
                )

        print(json.dumps(reports, indent=2))

        failures = []
        for report in reports:
            label = report["label"]
            before = report["before"]
            viewport_width = before["viewport"]["innerWidth"]
            for element_name in ("player", "controls", "bars"):
                if before[element_name]["width"] > viewport_width + 0.5:
                    failures.append(
                        f"{label}: {element_name} is {before[element_name]['width']}px wide in a {viewport_width}px viewport"
                    )
            if before["overlap"] or not before["barsBelowControls"]:
                failures.append(f"{label}: equalizer overlaps controls or is not below them")
            # Audio must start playing after click
            if report["afterPlay"]["ariaLabel"] != "Pause" or report["afterPlay"]["current"] == "0:00":
                failures.append(f"{label}: audio did not begin playing after click")
        if failures:
            raise AssertionError("\n".join(failures))


if __name__ == "__main__":
    asyncio.run(main())