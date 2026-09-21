"""
USD Thumbnail Generator
-----------------------
Generates thumbnails and cards for DPEL-hosted USD assets.

ASWF Dev Days Project
Author: Aden Thompson
"""
import math

from pxr import Usd, UsdMedia, Sdf, UsdGeom, Gf
import subprocess
import posixpath
import os
import numpy

# CONFIG
USDRECORD = r"D:\_apps\OpenUSD\26.08\bin\usdrecord"

PRIM_NAME = "decor_bonsai_jar01"
FOLDER_PATH = f"D:/ALab/ALab-2.3.0/ALab/entity/{PRIM_NAME}"
USDA_PATH = posixpath.join(FOLDER_PATH, f"{PRIM_NAME}.usda")
PREVIEW_PATH = posixpath.join(FOLDER_PATH, "preview", f"{PRIM_NAME}_preview.usda")

OUTPUT_DIR = posixpath.join(FOLDER_PATH, "preview", f"{PRIM_NAME}_preview")
OUTPUT_PATH = posixpath.join(OUTPUT_DIR, "thumbnail.png")

TEMP_RENDER_PATH = posixpath.join(FOLDER_PATH, f"{PRIM_NAME}_thumbgen_tmp.usda")

THUMBNAIL_DIMENSIONS = "1024 1024"


def create_stage(usda_path: str) -> Usd.Stage:
    stage = Usd.Stage.Open(usda_path)
    if not stage:
        raise RuntimeError(f"Stage not found at {usda_path}")
    return stage



def create_camera_in_stage(
        stage: Usd.Stage,
        camera_prim_path: str = "/ThumbnailCamera"
) -> UsdGeom.Camera:

    if stage.GetPrimAtPath(camera_prim_path):
        raise RuntimeError(f"Prim already exists at {camera_prim_path}; refusing to clobber it.")

    usd_camera = UsdGeom.Camera.Define(stage, Sdf.Path(camera_prim_path))
    usd_camera.CreateProjectionAttr().Set(UsdGeom.Tokens.perspective)
    usd_camera.CreateFocalLengthAttr().Set(35.0)
    usd_camera.CreateHorizontalApertureAttr().Set(20.955)
    usd_camera.GetFStopAttr().Set(0.0)
    return usd_camera



# Calculate the camera's orbit offset and up vector based on the stage's up-axis
def get_camera_offset(
        distance: float,
        azimuth: float,
        elevation: float,
        up_axis: str
) -> tuple[Gf.Vec3d, Gf.Vec3d]:

    # Y-up
    if up_axis == UsdGeom.Tokens.y:
        offset = Gf.Vec3d(
            distance * math.cos(elevation) * math.sin(azimuth),
            distance * math.sin(elevation),
            distance * math.cos(elevation) * math.cos(azimuth),
        )
        up_vector = Gf.Vec3d(0, 1, 0)
    # Z-up
    elif up_axis == UsdGeom.Tokens.z:
        offset = Gf.Vec3d(
            distance * math.cos(elevation) * math.sin(azimuth),
            distance * math.cos(elevation) * math.cos(azimuth),
            distance * math.sin(elevation),
        )
        up_vector = Gf.Vec3d(0, 0, 1)
    else:
        raise ValueError(f"Unsupported stage up axis: {up_axis}")

    return offset, up_vector



# Position and orient a camera to frame a USD prim based on its bounds
def frame_camera(
    stage: Usd.Stage,
    camera: UsdGeom.Camera,
    target_prim: Usd.Prim,
    azimuth_deg: float = 45.0,
    elevation_deg: float = 30.0,
    padding: float = 1.1,
) -> None:
    time = Usd.TimeCode.Default()

    # Find world-space bounds of all meshes
    min_point = Gf.Vec3d(float("inf"))
    max_point = Gf.Vec3d(float("-inf"))

    found_mesh = False

    for prim in Usd.PrimRange(target_prim):
        if not prim.IsA(UsdGeom.Mesh):
            continue

        mesh = UsdGeom.Mesh(prim)
        points = mesh.GetPointsAttr().Get(time)

        if not points:
            continue
        found_mesh = True

        # Convert USD points to a numpy array for efficiency
        points = numpy.asarray(points, dtype=numpy.float64)

        # Find local-space bounds
        local_min = points.min(axis=0)
        local_max = points.max(axis=0)

        # Transform the 8 corners of the local bounding box into world space
        # This avoids transforming every vertex individually
        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(time)

        for x in (local_min[0], local_max[0]):
            for y in (local_min[1], local_max[1]):
                for z in (local_min[2], local_max[2]):
                    point = matrix.Transform(
                        Gf.Vec3d(float(x), float(y), float(z))
                    )

                    min_point = Gf.Vec3d(
                        min(min_point[0], point[0]),
                        min(min_point[1], point[1]),
                        min(min_point[2], point[2]),
                    )

                    max_point = Gf.Vec3d(
                        max(max_point[0], point[0]),
                        max(max_point[1], point[1]),
                        max(max_point[2], point[2]),
                    )

    if not found_mesh:
        raise RuntimeError(f"No mesh geometry found under {target_prim.GetPath()}.")

    # Calculate target center and radius
    center = (min_point + max_point) / 2.0
    radius = (max_point - center).GetLength()

    if radius <= 0:
        raise RuntimeError("Target prim has zero-size bounds.")

    # Calculate camera distance from field of view
    camera_data = camera.GetCamera(time)

    fov_deg = camera_data.GetFieldOfView(Gf.Camera.FOVHorizontal)
    fov_rad = math.radians(fov_deg)

    distance = ( radius / math.sin(fov_rad / 2.0) ) * padding

    # Calculate camera orbit position
    up_axis = UsdGeom.GetStageUpAxis(stage)
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)

    offset, up_vector = get_camera_offset(distance, azimuth, elevation, up_axis)

    camera_position = center + offset

    # Aim camera at target
    view_matrix = Gf.Matrix4d()
    view_matrix.SetLookAt(camera_position, center, up_vector)

    # USD needs the camera's world transform
    world_matrix = view_matrix.GetInverse()

    # Apply transform to USD camera
    xformable = UsdGeom.Xformable(camera)
    xformable.ClearXformOpOrder()
    xformable.AddTransformOp().Set(world_matrix, time)



# Render and export thumbnail to path using usdrecord CLI command
def render_thumbnail(
        usda_path: str,
        output_png_path: str,
        camera: UsdGeom.Camera
) -> None:
    os.makedirs( os.path.dirname(output_png_path), exist_ok=True )

    cmd = [
        "cmd.exe",
        "/c",
        USDRECORD,
        "--camera",
        str(camera.GetPath()),
        os.path.normpath(usda_path),
        os.path.normpath(output_png_path)
    ]
    subprocess.run(cmd, check=True)



# Update the USDA file to apply the thumbnail dictionary
def update_usd_thumbnail(
        stage: Usd.Stage,
        thumbnail_path: str,
        target_prim: Usd.Prim
) -> None:
    asset_previews_api = UsdMedia.AssetPreviewsAPI.Apply(target_prim)
    thumbnail = UsdMedia.AssetPreviewsAPI.Thumbnails(Sdf.AssetPath(thumbnail_path))
    asset_previews_api.SetDefaultThumbnails(thumbnail)
    stage.GetRootLayer().Save()





def main():
    stage = create_stage(USDA_PATH)
    prim: Usd.Prim = stage.GetPrimAtPath("/root")
    if not prim:
        raise RuntimeError("Prim not found: /root")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    temp_camera = create_camera_in_stage(stage)
    frame_camera(stage, temp_camera, prim)

    try:
        stage.GetRootLayer().Export(TEMP_RENDER_PATH)

        render_thumbnail(
            TEMP_RENDER_PATH,
            OUTPUT_PATH,
            temp_camera
        )
        print(f"Rendered thumbnail: {OUTPUT_PATH}")

    finally:
        stage.RemovePrim(temp_camera.GetPath())
        if os.path.exists(TEMP_RENDER_PATH):
            os.remove(TEMP_RENDER_PATH)

    thumbnail_path = posixpath.join("preview", PRIM_NAME + "_preview", "thumbnail.png")
    update_usd_thumbnail(stage, thumbnail_path, prim)


if __name__ == "__main__":
    main()