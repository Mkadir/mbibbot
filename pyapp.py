from database.crud import add_user
from loader import app
from pyrogram import types, filters, Client, enums
from loader import db
from data.config import GROUP_ID
from pyrogram.types import ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus

from pyrogram import Client, filters, types


@app.on_chat_member_updated()
async def handle_bot_added(client: Client, chat_member_updated: ChatMemberUpdated):
    # Check if the bot has just been added to the group
    try:
        if (chat_member_updated.new_chat_member.status == ChatMemberStatus.MEMBER and
            chat_member_updated.old_chat_member is None):
            
            group_id = chat_member_updated.chat.id  # Get the group ID
            print(group_id)

            # Fetch all members of the new group
            members = client.get_chat_members(group_id)
            print("database updated")
            # Iterate over each member and save to database
            async for member in members:
                if member.user.is_bot or member.user.is_deleted:
                    continue  # Skip bots and deleted users

                user_id = member.user.id
                phone = member.user.phone_number if member.user.phone_number else None
                full_name = (member.user.first_name or '') + (member.user.last_name or '')
                username = member.user.username

                # Add user to the database
                add_user(
                    db=db,
                    tg_id=user_id,
                    full_name=full_name,
                    username=username,
                    phone_number=phone
                )
    except Exception as e:
        print(e)


@app.on_message(filters.new_chat_members)
async def new_member(client: Client, message: types.Message):
    for member in message.new_chat_members:
        if member.is_bot or member.is_deleted:
            continue

        user_id = member.id
        phone = member.phone_number if member.phone_number else None
        full_name = (member.first_name or '') + (member.last_name or '')
        username = member.username
        print("database updated")
        # Add or update user in the database
        add_user(
            db=db,
            tg_id=user_id,
            full_name=full_name,
            username=username,
            phone_number=phone
        )


@app.on_message(~filters.outgoing & filters.text & filters.regex(r'update'))
async def get_users(client: Client, message: types.Message):
    await message.delete()
    if message.chat.id == int(GROUP_ID):
        members = client.get_chat_members(message.chat.id)
        async for member in members:
            if member.user.is_bot or member.user.is_deleted:
                continue

            user_id = member.user.id
            phone = member.user.phone_number
            full_name = (member.user.first_name or '') + (member.user.last_name or '')
            username = member.user.username

            # Add or update user in the database
            add_user(
                db=db,
                tg_id=user_id,
                full_name=full_name,
                username=username,
                phone_number=phone
            )

if __name__ == "__main__":
    app.run()
