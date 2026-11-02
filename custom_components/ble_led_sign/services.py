SERVICE_NAMES = (
    "write",
    "send_text",
    "send_image",
    "send_animation",
    "send_jt",
    "set_icon",
    "set_music",
    "send_command",
)

# These read local files (image_path, jt_path, font) named by the caller, so
# they are admin only. Automations run without a user context and are unaffected.
ADMIN_SERVICE_NAMES = (
    "send_text",
    "send_image",
    "send_animation",
    "send_jt",
)
