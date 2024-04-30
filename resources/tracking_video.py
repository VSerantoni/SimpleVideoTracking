import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import cv2

from . import utils as ut

HEIGHT_SHOWN = 720                                             # height (in px) of the shown image - Only acts on displayed info, not on saved info

class TrackingVideo():
    
    def __init__(self, path2video: Path, name_video: str, time_start: str = '00:00', time_stop: str = '00:00', step_tracking: int = 0) -> None:
        """Initialize the tracking process

        Args:
            path2video (Path): path pointing to the video
            name_video (str): name of the video with extension
            time_start (str, optional): time of video at which tracking is to start. Defaults to '00:00'.
            time_stop (str, optional): time of video at which tracking is to stop. Defaults to '00:00' interpreted as last frame.
            step_tracking (int, optional): To avoid having to track every frame, step_tracking allows you to track only each frame at each step. Defaults to 0 corresponding to 2 tracking per second.
        """
        
        # Tracking on a selected time range
        self.time_start = ut.check_time_format(time_start, 'time_start')
        self.time_stop = ut.check_time_format(time_stop, 'time_stop')
        
        # Init the video    
        self.path = path2video
        self.name = name_video
        self.video = cv2.VideoCapture(str(self.path / self.name))
        self.check_video()
        
        # Metadata from the input video
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.nb_total_frame = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        print('\nMetadata:')
        print(f'    |- loaded video: {self.name}')
        print(f'    |- fps: {self.fps:.2f}')
        print(f'    |- total number of frame: {self.nb_total_frame}\n')
        
        # Parameters
        self.step_tracking = int(0.5*np.round(self.fps)) if step_tracking == 0 else step_tracking
        self.scaling_px2mm = 1                                              # size of 1 px in mm - updated only if 'px2mm()' is called
        
    def check_video(self):
        if not self.video.isOpened():
            print('=> Error: impossible to open the video file')
            exit(1)
            
    def get_frames2track(self):
        self.frame_start = int(self.fps*(int(self.time_start[:2])*60 + int(self.time_start[-2:])))
        self.frame_stop = int(self.fps*(int(self.time_stop[:2])*60 + int(self.time_stop[-2:])))
        if (self.frame_stop > self.nb_total_frame) or self.frame_stop == 0:
            self.frame_stop = self.nb_total_frame
        self.frames2track = np.arange(self.frame_start, self.frame_stop, self.step_tracking)
        self.nb_traited_frame = len(self.frames2track)
        
    def get_init_rois(self):
        self.get_frames2track()
        
        # Read first image
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.frame_start)
        _, frame_ref = self.video.read()
        self.gray_ref = cv2.cvtColor(frame_ref, cv2.COLOR_BGR2GRAY)
        
        # Resize (only acts on displayed info, not on saved info)
        self.h_frame, self.w_frame, _ = frame_ref.shape
        ratio_frame = self.w_frame/self.h_frame
        new_width = int(HEIGHT_SHOWN*ratio_frame)
        frame_ref_resized = cv2.resize(frame_ref, (new_width, HEIGHT_SHOWN))
        self.ratio_change = self.w_frame/new_width

        # Select ROI
        rois_coor_resized_frame = cv2.selectROIs('Select the ROIs', frame_ref_resized)
        cv2.destroyAllWindows()
        self.rois_coor_origin_frame = (self.ratio_change*rois_coor_resized_frame).astype(int)
        
        # Display selected ROIs on the first image
        ut.show_ROIs(frame_ref_resized, rois_coor_resized_frame, 'Tracked area')
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        test = input('Intial ROIs are well defined? (y/n) ')
        if test == 'n':
            print('\n/!\ Wrong definition of ROIs.')
            print('    Try again')
            input('\n<Hit Enter To Exit>')
            exit()
        
        self.nb_roi = self.rois_coor_origin_frame.shape[0]
        
    def px2mm(self, time_scaling2mm: str = '00:00'):
        """(optional) give the size of 1 px in mm using 1 frame with a visible ruler-like to click on.

        Args:
            time_scaling2mm (str, optional): time of video at which the ruler-like is visible . Defaults to '00:00'.
        """
        self.time_scaling2mm = ut.check_time_format(time_scaling2mm, 'time_scaling2mm')
        
        frame_scaling = int(self.fps*(int(self.time_scaling2mm[:2])*60 + int(self.time_scaling2mm[:2])))
        self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_scaling)
        _, frame_sc = self.video.read()
        h, w, c = frame_sc.shape
        frame_sc = cv2.resize(frame_sc, (int(w/self.ratio_change), int(h/self.ratio_change)))
        self.scaling_px2mm = ut.get_scaling(frame_sc, self.ratio_change)
    
    def track_rois(self, step_show: int = 1, step_update_ref: int = -1, scaling_SA: float = 0.5):
        """main loop tracking each ROI.

        Args:
            step_show (int, optional): Not useful to always diplay the tracking process, this parameter allow to display only every \'step_show\' tracking (enable much faster computation). Defaults to 1.
            step_update_ref (int, optional): Tracking process look for the first selected ROI. If these ROIs are changing during the video (rotation, scaling, ...) updating these ROIs is mandatory. Defaults to -1 for no updating, if needed, try 30-50 then, depending on the result, increase or decrease.
            scaling_SA (float, optional): parameter of the size of the area in which the ROI is searched. The Serch Area (SA) is centered on the ROI and expanded in all directions by scaling the width/height of the ROI by this parameter. Defaults to 0.5.
        """
        self.step_show = step_show                                                                     
        self.step_update_ref = step_update_ref 
        self.scaling_SA = scaling_SA            # width/height ZC (bigger than ZR and centered on it) = scaling_ZR*width_ZR + width_ZR + scaling_ZR*width_ZR
           
        # init the positions of the tracked ROIs
        self.tracked_positions = np.zeros((self.nb_traited_frame, self.nb_roi*self.rois_coor_origin_frame.shape[1]))
        for index, roi in enumerate(self.rois_coor_origin_frame):
            self.tracked_positions[0,4*index:4*index+4] = roi        
        
        # get the ROIs from the frame 'gray_ref' to follow (can change if update)
        self.all_rois_ref = ut.get_rois_ref(self.rois_coor_origin_frame, self.gray_ref)
        
        # init all counter
        count=1                     # index of the treated frame
        count_Delta = 1             # count if the searched ROI (roi_ref) must be updated. Update when count_Delta loop over 'step_update_ref'
        count_show = 1              # count if the frame is displayed or not (to spare cpu). Display when count_show loop over 'step_show'
        Color_green = True          # change the color of the ROIs when the reference images are updated. Start by green rectangle
        warning_SA = False          # print a warning if one SA is exiting the frame
        
        # main loop
        for sub_frame in self.frames2track[1:]:
            label_warning = ' => Warning: one SA is exiting the frame' if warning_SA else ''
            print('frame loaded: ', int(sub_frame), 'over ', int(self.frames2track[-1]), label_warning, end='\r')
            self.video.set(cv2.CAP_PROP_POS_FRAMES, sub_frame)
            _, frame = self.video.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # init the new coor in case of updating
            tmp_rects = np.zeros(self.rois_coor_origin_frame.shape, dtype=int)
            
            # loop over each ROI
            all_warning_SA = []
            for index in range(self.nb_roi):
                # get roi_ref (patern to find)
                roi_ref = self.all_rois_ref[index]                                                  # pattern to find in the SA
                
                # get roi_SA (Search Area in 'gray')
                x, y, w, h = self.tracked_positions[count-1, 4*index:4*index+4].astype(int)         # Last postion of the ROI
                w_scale = int(self.scaling_SA*w)
                h_scale = int(self.scaling_SA*h)
                roi_SA = gray[y-h_scale:y+h+h_scale, x-w_scale:x+w+w_scale]                         # Search Area (bigger than roi_ref)
                if (x+w+w_scale) > gray.shape[1]:
                    all_warning_SA.append(True)
                
                # find the new coordinate of the ROI
                result = cv2.matchTemplate(roi_SA, roi_ref, cv2.TM_CCOEFF_NORMED)
                _, _, _, max_loc = cv2.minMaxLoc(result)
                top_left = (x-w_scale + max_loc[0], y-h_scale + max_loc[1])
                
                # store the new coordinate            
                self.tracked_positions[count, 4*index:4*index+4] = np.array([top_left[0], top_left[1], w, h])
                tmp_rects[index,:] = np.array([top_left[0], top_left[1], w, h])
            
            # check if the_SA alert should be triggered
            if all_warning_SA:
                warning_SA = True
            else:
                warning_SA = False
                
            # update the reference image
            if count_Delta == self.step_update_ref:
                self.all_rois_ref = ut.get_rois_ref(tmp_rects, gray)
                count_Delta = 1
                Color_green = not(Color_green)          # switch color to indicate the update of the reference image
            else:
                count_Delta += 1
            
            if count_show == self.step_show:  
                tmp_ROIs_resized = ((1/self.ratio_change)*tmp_rects).astype(int)
                frame_resized = cv2.resize(frame, (int(self.w_frame/self.ratio_change), int(self.h_frame/self.ratio_change)))
                if Color_green:
                    ut.show_ROIs(frame_resized, tmp_ROIs_resized, 'Tracking...', color=(0, 255, 0))
                else:
                    ut.show_ROIs(frame_resized, tmp_ROIs_resized, 'Tracking...', color=(255, 0, 0))
                cv2.waitKey(1)   
                count_show = 1
            else:
                count_show += 1
            count += 1

        self.last_frame = gray       
        cv2.destroyAllWindows()

    def check_tracking(self):
        # Resize to display frames at the desired size
        gray_ref_resized = cv2.resize(self.gray_ref, (int(self.w_frame/self.ratio_change), int(self.h_frame/self.ratio_change)))
        last_frame_resized = cv2.resize(self.last_frame, (int(self.w_frame/self.ratio_change), int(self.h_frame/self.ratio_change)))
        tracked_position_resized = (1/self.ratio_change)*self.tracked_positions
        
        ut.plot_check(gray_ref_resized, last_frame_resized, tracked_position_resized)
        
        test = input('\nTracking Ok? (y/n) ')
        if test == 'n':
            print('\n/!\ Tracking failed.')
            print('    Try other parameters and/or ROIs')
            input('\n<Hit Enter To Exit>')
            exit()
        else:
            plt.close('all')

    def save_result(self):
        """Save the tracking result as \'tracked_positions_pixel.txt\' in the folder of the video.
        """
        s = input('\nSave ? (y/n) ')
        if s == 'y':
            ut.save_result_txt(self.path, self.tracked_positions, self.step_tracking, self.fps, self.scaling_px2mm)
