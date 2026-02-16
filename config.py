import discord

# Role IDs
ADMIN_ROLE_ID = 1472653727935496285
STAFF_ROLE_ID = 1471769220759945236
VERIFY_ROLE_ID = 1472316348771078275

# Category IDs
TICKET_CATEGORY_ID = 1471769129156349952
PAY_CATEGORY_ID = 1471769793433702462


def is_admin(user: discord.Member) -> bool:
    role_ids = {r.id for r in user.roles}
    return ADMIN_ROLE_ID in role_ids or STAFF_ROLE_ID in role_ids
