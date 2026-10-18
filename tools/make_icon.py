"""Creates assets/icon.ico from the Windows thread-spool emoji."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ricamo_facile.library import render_emoji  # noqa: E402

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icon.ico")
img = render_emoji("\U0001F9F5", 256)
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save(out.replace(".ico", ".png"))
print("written", os.path.normpath(out))
