## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2017 Intel Corporation. All Rights Reserved.

#####################################################
##              Align Depth to Color               ##
#####################################################

# First import the library
import pyrealsense2 as rs
# Import Numpy for easy array manipulation
import numpy as np
# Import OpenCV for easy image rendering
import cv2
import json


def loadConfiguration(profile, json_file):
    dev = profile.get_device()
    advnc_mode = rs.rs400_advanced_mode(dev)
    print("Advanced mode is", "enabled" if advnc_mode.is_enabled() else "disabled")
    json_obj = json.load(open(json_file))
    json_string = str(json_obj).replace("'", '\"')
    advnc_mode.load_json(json_string)

    while not advnc_mode.is_enabled():
        print("Trying to enable advanced mode...")
        advnc_mode.toggle_advanced_mode(True)

        # At this point the device will disconnect and re-connect.
        print("Sleeping for 5 seconds...")
        time.sleep(5)

        # The 'dev' object will become invalid and we need to initialize it again
        dev = profile.get_device()
        advnc_mode = rs.rs400_advanced_mode(dev)
        print("Advanced mode is", "enabled" if advnc_mode.is_enabled() else "disabled")
        advnc_mode.load_json(json_string)


# Create a pipeline

pipeline = rs.pipeline()

# Create a config and configure the pipeline to stream

#  different resolutions of color and depth streams

config = rs.config()

config.enable_stream(rs.stream.depth, 640, 360, rs.format.z16, 6)

config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 6)

# Start streaming

profile = pipeline.start(config)

# Getting the depth sensor's depth scale (see rs-align example for explanation)

depth_sensor = profile.get_device().first_depth_sensor()

depth_scale = depth_sensor.get_depth_scale()

print("Depth Scale is: ", depth_scale)

# We will be removing the background of objects more than

#  clipping_distance_in_meters meters away

clipping_distance_in_meters = 1  # 1 meter

clipping_distance = clipping_distance_in_meters / depth_scale

# Create an align object

# rs.align allows us to perform alignment of depth frames to others frames

# The "align_to" is the stream type to which we plan to align depth frames.

align_to = rs.stream.color

align = rs.align(align_to)

# Streaming loop

try:

    while True:

        # Get frameset of color and depth

        frames = pipeline.wait_for_frames()

        # frames.get_depth_frame() is a 640x360 depth image

        # Align the depth frame to color frame

        aligned_frames = align.process(frames)

        # Get aligned frames

        aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image

        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid

        if not aligned_depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data())

        color_image = np.asanyarray(color_frame.get_data())

        # Remove background - Set pixels further than clipping_distance to grey

        grey_color = 153

        depth_image_3d = np.dstack(
            (depth_image, depth_image, depth_image))  # depth image is 1 channel, color is 3 channels

        bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), grey_color, color_image)

        # Render images

        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        images = np.hstack((bg_removed, depth_colormap))

        cv2.namedWindow('Align Example', cv2.WINDOW_AUTOSIZE)

        cv2.imshow('Align Example', images)

        cv2.waitKey(1)

finally:

    pipeline.stop()
