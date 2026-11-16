import html as html_lib

DEFAULT_SUBJECT = "Привет от Stamp"

WRAPPER = """\
<!DOCTYPE html>
<html><body style="font-family: Arial, sans-serif; background:#f5f5f5; padding:24px;">
  <div style="max-width:560px; margin:0 auto; background:#fff; border-radius:12px;
              padding:32px; box-shadow:0 2px 12px rgba(0,0,0,.08);">
    <h2 style="color:#111;">Привет, это Stamp</h2>
    <p style="color:#444; line-height:1.6;">{body}</p>
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
    <p style="color:#999; font-size:12px;">Отправлено через Stamp</p>
  </div>
</body></html>
"""


def render(body: str, allow_html: bool = False) -> str:
    if allow_html:
        safe = body
    else:
        safe = html_lib.escape(body).replace("\n", "<br>")
    return WRAPPER.replace("{body}", safe)
