"""
USD Thumbnail Generator
-----------------------
Generatoes thumbnails and cards for DPEL-hosted USD assets.

ASWF Dev Days Project
Author: Aden Thompson
"""

from pxr import Usd, UsdMedia, Tf
import subprocess

# CONFIG

folder_path = r"D:\ALab\ALab-2.3.0\ALab\entity\book_encyclopedia01"
usda_path = r"D:\ALab\ALab-2.3.0\ALab\entity\book_encyclopedia01\book_encyclopedia01.usda"
USDRECORD = r"D:\_apps\OpenUSD\26.08\bin\usdrecord"


# SET STAGE AND GET TARGET PRIM

stage: Usd.Stage = Usd.Stage.Open(usda_path)

prim: Usd.Prim = stage.GetPrimAtPath("/root/GEO")

child_prim: Usd.Prim

if child_prim := prim.GetChild("encyclopedia01_M_hrc"):
    print("Child prim exists")
else:
    print("Child prim DOES NOT exist")


# RENDER THUMBNAIL

def render_thumbnail(usd_path, output_png_path, camera_path):
    cmd = [
        "cmd.exe",
        "/c",
        USDRECORD,
        "--camera", camera_path,
        usd_path,
        output_png_path
    ]

    subprocess.run(cmd, check=True)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main():
    # test rendering a full scene that has pre-existing camera on stage
    alab_full = r"D:\ALab\ALab-2.3.0\ALab\entry.usda"
    render_thumbnail(r"D:\ALab\ALab-2.3.0\ALab\entry.usda", r"D:\thumbnail2.png", "/root/camera01")
    print(f"Rendered thumbnail: thumbnail2.png")
    pass


if __name__ == "__main__":
    main()