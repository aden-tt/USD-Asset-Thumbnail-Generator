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

PRIM_NAME = "chemistry_beaker_rack01"
FOLDER_PATH = f"D:/ALab/ALab-2.3.0/ALab/entity/{PRIM_NAME}"
USDA_PATH = posixpath.join(FOLDER_PATH, f"{PRIM_NAME}.usda")
PREVIEW_PATH = posixpath.join(FOLDER_PATH, "preview", f"{PRIM_NAME}_preview.usda")

OUTPUT_DIR = posixpath.join(FOLDER_PATH, "preview", f"{PRIM_NAME}_preview")
OUTPUT_PATH = posixpath.join(OUTPUT_DIR, "thumbnail.png")

# Create and return a stage
def create_temp_stage(usda_path: str) -> Usd.Stage:
    stage: Usd.Stage = Usd.Stage.CreateInMemory(usda_path)
    if not stage:
        print("Stage not found!")
        exit(1)
    else:
        return stage

# Create and return a camera in the given stage
def create_camera_in_stage(stage: Usd.Stage, camera_prim_path: str="/World/MyPerspCam") -> UsdGeom.Camera:
    usd_camera = UsdGeom.Camera.Define(stage, Sdf.Path(camera_prim_path))
    usd_camera.CreateProjectionAttr().Set(UsdGeom.Tokens.perspective)
    return usd_camera


def frame_camera(stage: Usd.Stage, camera: UsdGeom.Camera) -> None:
    default_prim = UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
    stage.SetDefaultPrim(default_prim.GetPrim())

    # Export the complete Stage as a string and print it.
    usda = stage.GetRootLayer().ExportToString()
    print(usda)

    # Check that the camera was created
    prim = camera.GetPrim()
    assert prim.IsValid()
    assert prim.GetTypeName() == "Camera"
    projection = camera.GetProjectionAttr().Get()
    assert projection == UsdGeom.Tokens.perspective



# Render/export a thumbnail using usdrecord
def render_thumbnail(usd_path: str, output_png_path: str, camera: UsdGeom.Camera) -> None:
    cmd = [
        "cmd.exe",
        "/c",
        USDRECORD,
        "--camera",
        str(camera.GetPath()),
        usd_path,
        output_png_path
    ]
    subprocess.run(cmd, check=True)


# Apply thumbnail schema and update thumbnail to reference
def update_usd_thumbnail(thumbnail_path: str=posixpath.join("preview", PRIM_NAME + "_preview", "thumbnail.png") ) -> None:
    # Create stage to modify and save asset
    asset_stage: Usd.Stage = Usd.Stage.Open(USDA_PATH)
    if not asset_stage:
        print("Stage not found!")
        exit(1)

    prim: Usd.Prim = asset_stage.GetPrimAtPath("/root")
    if not prim:
        print("Prim is null")
        exit(1)

    assetPreviewsAPI = UsdMedia.AssetPreviewsAPI.Apply(prim)
    if not prim.HasAPI(UsdMedia.AssetPreviewsAPI):
        print("AssetPreviewsAPI schema not applied successfully!")
        exit(1)

    thumbnail = UsdMedia.AssetPreviewsAPI.Thumbnails(thumbnail_path)
    if not thumbnail:
        print("invalid!!")
        exit(1)

    assetPreviewsAPI.SetDefaultThumbnails(thumbnail)

    asset_stage.GetRootLayer().Save()

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    # alab_full = r"D:\ALab\ALab-2.3.0\ALab\entry.usda"
    temp_stage = create_temp_stage(USDA_PATH)
    temp_camera = create_camera_in_stage(temp_stage)
    frame_camera(temp_stage, temp_camera)
    render_thumbnail(USDA_PATH, OUTPUT_PATH, temp_camera) # test render book
    print(f"Rendered thumbnail: {OUTPUT_PATH}")
    update_usd_thumbnail()


if __name__ == "__main__":
    main()