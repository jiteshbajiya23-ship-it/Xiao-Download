"""Helpers for revoking links."""


async def revoke_link(client, msg_id: int) -> bool:
    """Delete the file from LOG_CHANNEL -> the download link stops working."""
    from info import LOG_CHANNEL
    await client.delete_messages(LOG_CHANNEL, int(msg_id))
    try:
        from plugins.route import class_cache
        for streamer in class_cache.values():
            streamer.cached_file_ids.pop(int(msg_id), None)
    except Exception:
        pass
    return True
