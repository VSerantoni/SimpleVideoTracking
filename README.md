# Simple-VideoTracking
***Simple-VideoTracking*** is a tracking tool easy to use. It is based on ZNCC (Zero mean Normalized Cross-Correlation) criterion and can track in parallel several Region of Interest (RoI). Users can generate a single txt file summarizing the details and the followed path of each RoI.

This code is illustrated in `demo.py`.

Warning: this tool is efficient but basic. The tracking process is done on gray level, therfore, tracking a RoI with many details on the background or being 'visible' only by color contrast can lead to major difficulties.

## Structure
*Simple-VideoTracking* is structured based on a unique Class named `TrackingVideo`.
```
track = TrackingVideo(path2video, name_video, time_start = '00:00', time_stop = '00:00', step_tracking = 0) (main classe)
|   - track.get_init_rois()
|   - (optional) track.px2mm(time_scaling2mm = '00:00')
|   - track.track_rois(step_show = 1, step_update_ref = -1, scaling_SA = 0.5)
|   - track.check_tracking()   
|   - track.save_result()
```

## Working Principle
1. Define the path and the name of the video to study.<br>
_optional parameters:_ `time_start`, `time_stop`, `step_tracking`.
2. `get_init_rois()` enables to select all wanted RoIs on a single frame of the video. The selected frame correspond to the one defined by `time_start`.<br>
    - To select a RoI on the open frame, click and drag to draw the RoI. Press the space bar to confirme the selection.<br>
    - Repeat this step for all RoI then press escape to end the selection process.<br>
    - A window open summarizing all selected RoI.
3. `track_rois()` start the tracking process while showing all updated tracked RoI.<br>
_optional parameters:_ `step_show`, `step_update_ref`, `scaling_SA`.
    - Once the tracking is done, run `check_tracking()` to visualize the final location of all RoIs.
4. (optional) `px2mm()` enables to evaluate the size of 1 pixel in _mm_.
_parameter:_ `time_scaling`.
    - A window with the selected frame open. Click on two (2) points then indicate on the prompt the distance in _mm_ between these two points.
5. `save_result()` generates the txt file summarizing the size and location of each initial RoI, the size of 1 px and the followed path.

## Details

**TrackingVideo (main classe)**
```
track = TrackingVideo(path2video: Path, name_video: str, time_start: str = '00:00', time_stop: str = '00:00', step_tracking: int = 0)
```

Initialize the tracking tool.

+ `path2video (Path)`: path of the video defined using the `Path` module.
+ `name_video (str)`: complet name of the video with the extension.
+ `time_start (str, optional)`: a string representing the time of the video when the tracking must start. Default is '00:00'
+ `time_stop (str, optional)`: a string representing the time of the video when the tracking must stop. Default is '00:00', a key string indicating to track until the end of the video.
+ `step_tracking (int, optional)`: an integer representing the **frame step** between each tracking process. If the displacement is slow and the video is filmed with *n* fps, tracking each RoIs in each frame is not mandatory, performing the tracking process on 1 or 2 frames per second can be enough. Defaults is two tracking per second (`int(0.5*np.round(nb_fps))`).

**track.get_init_rois**
```
get_init_rois()
```

Allow to select the RoIs to track.


**track.px2mm (optional)**
```
px2mm(time_scaling2mm: str = '00:00')
```

Give the size of 1 px in *mm* using a reference frame.

+ `time_scaling2mm (str, optional)`: time of the video at which the object with a known size is visible . Defaults to '00:00'.


**track.track_rois**
```
track_rois(step_show: int = 1, step_update_ref: int = -1, scaling_SA: float = 0.5)
```

Main loop tracking each RoI.

+ `step_show (int, optional)`: Showing the result of the tracking process for each loop is not necessary, this parameter allow to display only every \'step_show\' frame tracked (enable much faster computation). Defaults to 1.
+ `step_update_ref (int, optional)`: The tracking process is searching for the first selected RoI. If these RoIs are changing during the video (rotation, scaling, ...) updating these searched RoIs is necessary. Defaults to -1 for no updating, if needed, try at first 30-50 then adjust depending on the result.
+ `scaling_SA (float, optional)`: parameter of the size of the area in which the RoI is searched. The Serch Area (SA) is centered on the RoI and expanded in all directions by scaling the width/height of the RoI by this parameter. Defaults to 0.5.


**track.check_tracking**
```
check_tracking()
```

Check the tracking quality by showing the selected RoIs on the first frame and the identified RoIs on the last frame with the followed path.


**track.save_result**
```
save_result()
```

Save the tracking result as 'tracked_positions_pixel.txt' in the folder of the video. The following information are saved: locations and sizes of all initial RoIs, time vector and size of 1 pixel.
+ The size is width and height in pixel.
+ The saved displacements (x and y) correspond to the top left corner (as saved by the tool cv2.selectROIs)
