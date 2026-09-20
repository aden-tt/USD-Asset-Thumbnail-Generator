"""
USD Thumbnail Generator
-----------------------
Generates thumbnails and cards for DPEL-hosted USD assets.

ASWF Dev Days Project
Author: Aden Thompson


to-do:
 - ask ASFW what path to output thumbnails and previews
 - create camera and properly frame the asset
 - convert from hardcoded paths to user input
 - take multiple usda args

"""

from pxr import Usd, UsdMedia, Sdf, UsdGeom
import subprocess
import posixpath

# CONFIG
USDRECORD = r"D:\_apps\OpenUSD\26.08\bin\usdrecord"

PRIM_NAME = "books_magazines01"
FOLDER_PATH = f"D:/ALab/ALab-2.3.0/ALab/entity/{PRIM_NAME}"
USDA_PATH = posixpath.join(FOLDER_PATH, f"{PRIM_NAME}.usda")
PREVIEW_PATH = posixpath.join(FOLDER_PATH, "preview", f"{PRIM_NAME}_preview.usda")

OUTPUT_DIR = posixpath.join(FOLDER_PATH, "preview", f"{PRIM_NAME}_preview")
OUTPUT_PATH = posixpath.join(OUTPUT_DIR, "thumbnail.png")


# SET STAGE AND GET TARGET PRIM

stage: Usd.Stage = Usd.Stage.Open(USDA_PATH)
if not stage:
    print("Stage not found!")
    exit(1)

prim: Usd.Prim = stage.GetPrimAtPath("/root")
if not prim:
    print("Prim is null")
    exit(1)


# Render a thumbnail using usdrecord
def render_thumbnail(usd_path: str, output_png_path: str, camera_p: str="/World/MyPerspCam"):
    cmd = [
        "cmd.exe",
        "/c",
        USDRECORD,
        "--camera", camera_p,
        usd_path,
        output_png_path
    ]

    subprocess.run(cmd, check=True)

# Apply thumbnail schema and update thumbnail to reference
def update_usd_thumbnail():
    assetPreviewsAPI = UsdMedia.AssetPreviewsAPI.Apply(prim)
    if not prim.HasAPI(UsdMedia.AssetPreviewsAPI):
        print("AssetPreviewsAPI schema not applied successfully!")
        exit(1)

    thumbnail_path = posixpath.join("preview", PRIM_NAME + "_preview", "thumbnail.png")

    thumbnail = UsdMedia.AssetPreviewsAPI.Thumbnails(thumbnail_path)
    if not thumbnail:
        print("invalid!!")
        exit(1)

    assetPreviewsAPI.SetDefaultThumbnails(thumbnail)

    stage.GetRootLayer().Save()

#
def create_perspective_camera(stage: Usd.Stage, prim_path: str="/World/MyPerspCam") -> UsdGeom.Camera:
    camera_path = Sdf.Path(prim_path)
    usd_camera: UsdGeom.Camera = UsdGeom.Camera.Define(stage, camera_path)
    usd_camera.CreateProjectionAttr().Set(UsdGeom.Tokens.perspective)
    return usd_camera




# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():


    default_prim = UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
    stage.SetDefaultPrim(default_prim.GetPrim())

    # Create the perspective camera at /World/MyPerspCam
    cam_path = default_prim.GetPath().AppendPath("MyPerspCam")
    camera = create_perspective_camera(stage, cam_path)

    # Export the complete Stage as a string and print it.
    usda = stage.GetRootLayer().ExportToString()
    print(usda)

    # Check that the camera was created
    prim = camera.GetPrim()
    assert prim.IsValid()
    assert camera.GetPath() == Sdf.Path(cam_path)
    assert prim.GetTypeName() == "Camera"
    projection = camera.GetProjectionAttr().Get()
    assert projection == UsdGeom.Tokens.perspective

    # alab_full = r"D:\ALab\ALab-2.3.0\ALab\entry.usda"
    render_thumbnail(USDA_PATH, OUTPUT_PATH) # test render book
    print(f"Rendered thumbnail: {OUTPUT_PATH}")

    stage.RemovePrim(camera.GetPath())
    update_usd_thumbnail()


if __name__ == "__main__":
    main()