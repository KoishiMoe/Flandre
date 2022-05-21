from .sqlite import sqlite_pool

__all__ = ["NoteMatcher", "get_notes", "get_group_notes", "add_note", "delete_note", "mute", "unmute"]


class NoteMatcher:
    def __init__(self, note_id: str, note_type: str, content: str, resp: str, at: bool = False):
        self.id = note_id
        self.type = note_type
        self.content = content
        self.resp = resp
        self.at = at


async def get_notes(gid: int) -> list[NoteMatcher]:
    notes = []
    global_notes = await get_group_notes(0)
    if gid != 0:
        notes = await get_group_notes(gid)
        muted = await sqlite_pool.fetch_all("select noteID from mute where gid=:gid", {"gid": gid})
        muted = [i[0] for i in muted if i]
        if muted:
            for note in global_notes:
                if note.id in muted:
                    global_notes.remove(note)
    notes += global_notes

    return notes


async def get_group_notes(gid: int) -> list[NoteMatcher]:
    notes = []
    for note in await sqlite_pool.fetch_all("select noteID, type, matcherContent, resp, at from notes where gid=:gid",
                                            {"gid": gid}):
        notes.append(NoteMatcher(note[0], note[1], note[2], note[3], note[4]))

    return notes


async def add_note(gid: int, mtype: str, content: str, resp: str, at: bool) -> int:
    (note_id, ) = await sqlite_pool.fetch_one("select max(noteID) from notes where gid=:gid", {"gid": gid})
    note_id = 1 if not note_id else note_id + 1
    await sqlite_pool.execute("insert into notes values (:gid, :note_id, :type, :content, :resp, :at)",
                              {"gid": gid, "note_id": note_id, "type": mtype,
                               "content": content, "resp": resp, "at": at})
    return note_id


async def delete_note(gid: int, note_id: int):
    await sqlite_pool.execute("delete from notes where gid=:gid and noteID=:note_id", {"gid": gid, "note_id": note_id})


async def mute(gid: int, note_id: int):
    await sqlite_pool.execute("insert into mute values (:gid, :note_id) on conflict (gid, noteID) do nothing ",
                              {"gid": gid, "note_id": note_id})


async def unmute(gid: int, note_id: int):
    await sqlite_pool.execute("delete from mute where gid=:gid and noteID=:note_id", {"gid": gid, "note_id": note_id})
