"""Automatically kick deleted accounts

Will check active groups/channels periodically for deleted accounts, and then kick them.
"""

from telethon import client, events, sessions, errors
from .global_functions import log, cooldown
from asyncio import sleep


kick_counter = "kick_counter.txt"
deleted_admin = set()


@events.register(events.NewMessage(func=lambda e: not e.is_private))
@cooldown(60 * 60, False) # Only activate at minimum once an hour
async def kick_deleted(event):
    group = await event.get_chat() # Get group object
    kicked_users = 0

    response = list()
    async for user in event.client.iter_participants(group.id): # iterate over group members
        if not user.deleted: #  If it's a deleted account; kick
            continue
        if user.id in deleted_admin:
            continue
        try:
            await event.client.kick_participant(group, user)
            kicked_users += 1
        except errors.ChatAdminRequiredError:
            response.append(await event.respond(
                                "ChatAdminRequiredError:  "
                                + "I must have the ban user permission to be able to kick deleted accounts."
                                + "Please add me back as an admin."))
            await log(event, "Invalid permissions")
            await event.client.kick_participant(group, "me")
            break
        except errors.UserAdminInvalidError:
            deleted_admin.add(user.id)
            response.append(await event.respond(
                                "UserAdminInvalidError:  "
                                + "An admin has deleted their account, so I cannot kick it from the group."))

    if kicked_users >= 0:
        await log(event, f"Kicked {kicked_users}")

    with open(kick_counter) as f: # Get the old value of kicked deleted accounts
        old_kicked = f.read()
        if not old_kicked:
            old_kicked = 0
    with open(kick_counter, "w") as f: # Write new value
        new_val = kicked_users + int(old_kicked)
        f.write(str(new_val))

    if not response:
        return

    await sleep(60)
    try:
        for m in response:
            await m.delete()
    except errors.ChannelPrivateError:
        return
