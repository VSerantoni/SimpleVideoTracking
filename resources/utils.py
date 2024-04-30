import numpy as np
import matplotlib.pyplot as plt
# from matplotlib import cm
import cv2
from pathlib import Path

def check_time_format(time_format_tested: str, label: str) -> str:
    """check the time format that must be mm:ss

    Args:
        time_format_tested (str): input time
        label (str): name of the tested time

    Returns:
        str: time if the test is successful
    """
    try:
        int(time_format_tested[:2])
        int(time_format_tested[-2:])
        # self.time_start = time_start            # default is '00:00', leading to select the first frame
    except:
        print(f'=> {label}: invalid format. Excpected format \'mm:ss\' - 01:09 for 1m and 9s')
        exit()
    return time_format_tested
    
def show_ROIs(frame: np.ndarray, rois: np.ndarray, title: str, color: tuple = (255, 0, 0)) -> None:
    """Generate an image showing on 'frame' the location of the previously selected ROIs

    Args:
        frame (np.ndarray): frame from displaying ROIs
        rois (np.ndarray): location and size of each ROIs (first roi: rois[0,:]=x, y, width, height; where x and y are top left corner of the rectangle)
        title (str): title of the window
        color (tuple, optional): color of the ractangle in BGR
    """
    for index, roi in enumerate(rois):
        x, y, w, h = roi.astype(int)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
    cv2.imshow(title, frame)

def get_scaling(frame_scaling: np.ndarray, ratio_change: float) -> float:
    """Get the scaling factor to convert pixel to mm

    Args:
        frame_scaling (np.ndarray): frame used to get the correct scale
        ratio_change (float): scaling factor to draw an image with a previously indicated height

    Returns:
        scaling_px2mm (float): the scaling factor (1 px = 'scaling_px2mm' mm)
    """
    fig = plt.figure(figsize=(7*16/9, 7))
    plt.title('Select 2 points for scaling')
    plt.imshow(frame_scaling, cmap='gray')
    pts = np.round(plt.ginput(2,0)).astype(int)
    plt.close(fig)

    L_px = np.sqrt((pts[1][0]-pts[0][0])**2 + (pts[1][1]-pts[0][1])**2)
    L_mm = float(input('Length between the 2 selected points (in mm) : '))
    scaling_px2mm = L_mm/(ratio_change*L_px)
    return scaling_px2mm

def get_rois_ref(coor_ROIs: np.ndarray, gray_frame: np.ndarray) -> list:
    """get all ROIs (sub-part of the frame to find/track) from 'gray_frame'

    Args:
        coor_ROIs (np.ndarray): coordinates of all ROIs to track (stored x, y, width, height; where x and y are top left corner of the rectangle)
        gray_frame (np.ndarray): gray frame from which to extract the ROIs

    Returns:
        all_rois_ref (list): list of all ROIs (sub-part of the frame to find/track)
    """
    all_rois_ref = []
    for index, roi in enumerate(coor_ROIs):
        x_ref, y_ref, w_ref, h_ref = roi
        try:
            roi_ref = gray_frame[y_ref:y_ref+h_ref, x_ref:x_ref+w_ref]
        except:
            print('Error: updating the RoI with boundaries bigger than the frame is impossible')
            exit()
        all_rois_ref.append(roi_ref)
    return all_rois_ref

def plot_check(gray_origin: np.ndarray, last_frame: np.ndarray, tracked_position: np.ndarray) -> None:
    """Show the ROIs tracked on the first and last frame to check the tracking

    Args:
        gray_origin (np.ndarray): first frame tracked
        last_frame (np.ndarray): last frame tracked
        tracked_position (np.ndarray): all tracked coordinates
    """
    nb_roi = int(tracked_position.shape[1]/4)
    
    plt.figure(1, figsize=(8*16/9,8))
    plt.clf()
    plt.subplot(221)
    plt.title('Reference points')
    plt.imshow(gray_origin, cmap='gray')
    for n in range(nb_roi):
        plt.plot(tracked_position[0,4*n]+0.5*tracked_position[0,4*n+2], tracked_position[0,4*n+1]+0.5*tracked_position[0,4*n+3], 'r.', markersize = 5)
    
    plt.subplot(222)
    plt.title(f'Last identified points')
    plt.imshow(last_frame, cmap='gray')
    for n in range(nb_roi):
        plt.plot(tracked_position[-1,4*n]+0.5*tracked_position[-1,4*n+2], tracked_position[-1,4*n+1]+0.5*tracked_position[-1,4*n+3], 'b.', markersize = 5)

    plt.subplot(212)
    plt.title('Identified path of the tracked points')
    plt.imshow(gray_origin, cmap='gray')
    for n in range(nb_roi):
        plt.plot(tracked_position[:,4*n]+0.5*tracked_position[:,4*n+2], tracked_position[:,4*n+1]+0.5*tracked_position[:,4*n+3], '.')
        plt.plot(tracked_position[0,4*n]+0.5*tracked_position[0,4*n+2], tracked_position[0,4*n+1]+0.5*tracked_position[0,4*n+3], 'r.', markersize = 5)
        plt.plot(tracked_position[-1,4*n]+0.5*tracked_position[-1,4*n+2], tracked_position[-1,4*n+1]+0.5*tracked_position[-1,4*n+3], 'b*', markersize = 5)
    plt.show(block=False)
    
def save_result_txt(path: Path, tracked_positions: np.ndarray, step_tracking: int, fps: float, scaling_px2mm: float) -> None:
    """save the coordinates of the tracked ROIs, the size of each ROIs and the size of one pixel

    Args:
        path (Path): path towards the video
        tracked_positions (np.ndarray): all tracked coordinates
        step_tracking (int): step used to track only each frame step
        fps (float): frames per second
        scaling_px2mm (float): scaling factor of one pixel (1 px = 'scaling_px2mm' mm)
    """
    name_save = 'tracked_positions_pixel.txt'
            
    time_vector = np.zeros(tracked_positions.shape[0])
    nb_roi = int(tracked_positions.shape[1]/4)
    for index, _ in enumerate(time_vector[1:]):
        time_vector[index+1] = time_vector[index]+1000*step_tracking/fps

    header1 = ' ; '.join([f'w h' for i in range(nb_roi)])
    header2 = ' ; '.join([f'x y' for i in range(nb_roi)])
    
    w_h_index = []
    for i in range(nb_roi):
        w_h_index.extend([i*4+2, i*4+3])
    L = tracked_positions[0,w_h_index]
    L_str = ', '.join(str(int(item)) for item in L)
    
    with open(path / name_save, 'w') as f:
        f.write(header1+'\n')
        f.write(L_str+'\n')
        
        x_w_index = [item-2 for item in w_h_index]
        f.write(f'{header2} ; time(ms) ; Scaling (1 px = {scaling_px2mm:.4f} mm)' + '\n')
        for index, row in enumerate(tracked_positions):
            L = row[x_w_index]
            L = np.append(L, time_vector[index])
            L_str = ', '.join([str(int(x)) if i < 4 else f'{x:.2f}' for i, x in enumerate(L)])
            f.write(L_str+'\n')
