def build_patrol(type, system, coords, instructions, url, event=None):
    return {
        "type": type,
        "system": system,
        "coords": coords,
        "instructions": instructions,
        "url": url,
        "event": event,
    }
