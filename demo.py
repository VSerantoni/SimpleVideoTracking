from pathlib import Path

from resources.tracking_video import TrackingVideo

if __name__ == '__main__':
    '''
    Follow as many Regio Of Interest (ROI) as wanted in a video.
    Working on gray level.
    If requested, a file named 'tracked_positions_pixel.txt' is saved in the folder 'path2video'.
    '''
    
    path2video = Path.cwd() / 'test'
    video2study = 'video-test.mp4'          # accepted format: the format read by open-cv
    
    # Time range
    time_start = '00:10'
    time_stop = '00:50'
    
    track = TrackingVideo(path2video, video2study, time_start=time_start, time_stop=time_stop)
    
    track.get_init_rois()
    # track.px2mm(time_scaling2mm='00:05')
    track.track_rois(step_update_ref=20)
    track.check_tracking()
    track.save_result()