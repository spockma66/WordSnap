import numpy as np
import time
import subprocess
import sys
import cv2
import re
import threading
import globals  
from utils import load_config, logger
from book_ui import BookUI
from rapidocr_onnxruntime import RapidOCR
from PIL import Image, ImageDraw
from sklearn.cluster import DBSCAN
from io import BytesIO


def capture_image(book_ui):
    logger.info("Image capture started")
    
    config = load_config()
    camera_resolutions = config.get('camera_resolutions')
    selected_resolution_key = config.get('selected_resolution')
    width = camera_resolutions[selected_resolution_key]['width']
    height = camera_resolutions[selected_resolution_key]['height']
    camera_type = config.get('camera_type')
    logger.info("Config loaded")
    
    if camera_type == 'usbcam':
        usbcam_path = config.get('usbcam_path')
        command = ["fswebcam", "-d", str(usbcam_path), "-r", str(width) + "x" + str(height), "--no-banner", "-"]
    elif camera_type == 'rpicam':
        camera_settings = config.get('camera_settings')
        gain = camera_settings['gain']
        shutter = camera_settings['shutter']
        command = ["rpicam-still", "-o", "-", "--nopreview", "on", "--gain", str(gain), "--shutter", str(shutter), f"--width", str(width), f"--height", str(height)]
    else:
        logger.critical("The following camera type is not yet supported: %s", camera_type)
        error_texts = [f"The following camera type is not yet supported: {camera_type}. Please follow the instruction on the right side and restart this program"]
        error_texts.append("Please set the config value of 'camera_type' to 'usbcam' for a web camera with a usb cable, or set it to 'rpicam' for a raspberry pi camera that works with 'rpicam-still' command")
        book_ui.show_spread(error_texts)
        globals.CLOSING = True
        sys.exit(1)
        
        
    logger.debug("Command ready: %s", command)
    process = subprocess.run(command, capture_output=True)
    logger.info('Command executed')

    if process.returncode == 0:
        stream = BytesIO(process.stdout)
        stream.seek(0)
        image_data = np.frombuffer(stream.getvalue(), dtype=np.uint8)

        if image_data is not None and len(image_data) > 0:
            image = cv2.imdecode(image_data, flags=cv2.IMREAD_COLOR)     
            logger.info("Image captured")
            return image
        else:
            logger.critical("Captured empty image")
            error_texts = [f"Image capture failed. Please follow the instruction on the right side and restart this program"]
            if camera_type == 'usbcam':
                error_texts.append("Please check the usb connection of your camera and the config value of 'usbcam_path'. Use 'lsusb' command to list all usb connections and 'v4l2-ctl --list-devices' to list all camera paths")
            elif camera_type == 'rpicam':
                error_texts.append("Please check the physical connection of your raspberry pi camera")
            book_ui.show_spread(error_texts)
            globals.CLOSING = True
            sys.exit(1)
    else:
        logger.error("Error occurred when capturing image: %s", process.stderr.decode())
        return None


def orb_similarity(img1, img2):
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    if len(img2.shape) == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create()
    keypoints1, descriptors1 = orb.detectAndCompute(img1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(img2, None)

    if descriptors1 is None or descriptors2 is None:
        return 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors1, descriptors2)
    matches = sorted(matches, key=lambda x: x.distance)

    num_matches = len(matches)
    max_possible_matches = min(len(keypoints1), len(keypoints2))
    match_score = num_matches / max_possible_matches
    
    logger.debug("The matching score of images is: %s", match_score)
    return match_score


def is_text_useless(text):
    pattern = re.compile(r'''
            ^                                 # start
            (?!.*[A-Za-z].*[A-Za-z])          # negative lookahead, make sure there is only one letter in the matched string at most
            (?:                               # non-capturing group, match any case below
                [^A-Za-z0-9]+                   # 1. Pure English symbols(non-alphanumeric characters) in arbitrary length
                | \d+                           # 2. Digits in arbitrary length
                | [A-Za-z]                      # 3. Single English letter
            )+                                # one or more times allowed for the cases above
            $                                 # end
        ''', re.VERBOSE)
    
    return pattern.match(text)


def get_clusters(ocr_result):
    logger.info("Clustering started")
    
    config = load_config()
    black_list = config.get('black_list')
    epsilon = config.get('epsilon')
    logger.info("Config loaded")
    
    rectangles = []
    for rect in ocr_result:
        if rect[1] in black_list:
            continue
        x_min = min(p[0] for p in rect[0])
        y_min = min(p[1] for p in rect[0])
        x_max = max(p[0] for p in rect[0])
        y_max = max(p[1] for p in rect[0])
        rectangles.append((x_min, y_min, x_max, y_max, rect[1]))

    rectangles.sort(key=lambda r: r[0])

    # Assigning rectangles to different columns
    columns = []
    for i, (x_min, y_min, x_max, y_max, content) in enumerate(rectangles):
        if not columns or x_min > max(box[2] for box in columns[-1]):
            # Creating a new column and assign the first rectangle
            columns.append([((x_min, y_min, x_max, y_max, content))])
        else:
            # Assigning the current rectangle to the rightmost column
            columns[-1].append((x_min, y_min, x_max, y_max, content))
    logger.debug("Columns are: %s", columns)
    
    # Clustering with DBSCAN based on the columns
    final_clusters = []
    for i, col in enumerate(columns):
        y_coords = np.array([y_min for x_min, y_min, x_max, y_max, content in col])
        clustering = DBSCAN(eps=epsilon, min_samples=1).fit(y_coords.reshape(-1, 1))
        labels = clustering.labels_
        final_clusters.append([])
        for j, rect in enumerate(col):
            final_clusters[i].append((rect, labels[j]))
     
    logger.debug("Final clusters are: %s", final_clusters)
    logger.info("Clustering ended")
    return final_clusters
    
    
def show_rectangles(image, clusters):
    # Drawing rectangles on the image in test mode
    img = Image.fromarray(image)
    draw = ImageDraw.Draw(img)
    colors = ["red", "green", "blue", "yellow", "brown", "coral", "deepskyblue", "grey", "indigo", "gold", "tan", "tomato", "violet"]
    
    for col in clusters:    
        for (x_min, y_min, x_max, y_max, content), label in col:
            cluster_color = colors[label % len(colors)]
            draw.rectangle([x_min, y_min, x_max, y_max], outline=cluster_color, width=2)
    img.show()


def post_process(image, ui):
    logger.info("Image processing started")
    
    config = load_config()
    ocr_model_path = config.get('ocr_model_path')
    mode = config.get('current_mode')
    logger.info("Config loaded")
    
    engine = RapidOCR(rec_model_path=ocr_model_path)
    result, elapse = engine(image)
    logger.debug("OCR result generated: %s", result)
    
    if not result:
        logger.info("Image processing ended because no content was recognized")
        return
    
    # Get clusters of text rectangles to prepare for generating readable content 
    clusters = get_clusters(result)
    
    # Deciding it's in normal or test mode
    if mode == "normal":
        # Sorting text snippets from each rectangle and concatenating them by cluster
        logger.info("Processing ocr result in normal mode")
        text_segments = []
        for col in clusters:
            for label in set(label for rect, label in col):
                contents = [(y_max, content) for x_min, y_min, x_max, y_max, content in [rect for rect, lbl in col if lbl == label]]
                sorted_contents = sorted(contents)
                texts = " ".join(content for _, content in sorted_contents)
                logger.debug("Generated texts: %s", texts)
                
                # If a concatenated text doesn't contain any word, then it will be marked as 'useless'
                if is_text_useless(texts):
                    logger.debug("Texts useless and abandoned")
                    continue
                
                text_segments.append((len(texts), texts))
                logger.debug("Current text segments are: %s", text_segments)
        
        # Sorting concatenated text segments by length to show important content in the first two pages
        sorted_text_segments = sorted(text_segments, reverse=True)
        logger.debug("Final sorted text segments are: %s", sorted_text_segments)
        
        if not globals.CAPTURE_PAUSED and not globals.EXPLAINING and not globals.CLOSING:
            logger.info("Processing ocr result ended")
            texts = list(text_segment for _, text_segment in sorted_text_segments)
            ui.show_spread(texts)
        else:
            logger.warning("Image processing not finished due to paused capture or word explaining")
            raise NotImplementedError("New image was not processed")
    else:  
        logger.info("Processing ocr result in test mode - showing an image with boxes of text")
        show_rectangles(image, clusters)
    
    logger.info("Image processing ended")
    

def gen_loop(book_ui):
    logger.info("The main loop of image capture and processing started")
    
    config = load_config()
    interval_seconds = config.get('interval_seconds')
    similarity_threshold = config.get('similarity_threshold')
    logger.info("Config loaded")
    
    prev_image = None
    while not globals.CLOSING:
        if not globals.CAPTURE_PAUSED and not globals.EXPLAINING:
            curr_image = capture_image(book_ui)
            curr_image_processed = True
            
            if curr_image is not None and prev_image is not None:
                change_detected = (orb_similarity(prev_image, curr_image) < similarity_threshold)
                logger.debug("Current similarity threshold is: %s", similarity_threshold)
                logger.debug("Change detected: %s", change_detected)
                
                # If the current image is different from the previous one, then start processing the new image
                if change_detected:
                    try:
                        post_process(curr_image, book_ui)
                    except NotImplementedError as e:
                        curr_image_processed = False
            elif prev_image is None:
                try:
                    post_process(curr_image, book_ui)
                except NotImplementedError as e:
                    curr_image_processed = False
            
            if curr_image_processed:
                prev_image = curr_image
            
            logger.info("Sleeping for %s seconds by default", interval_seconds)
        else:
            logger.info("Sleeping for %s seconds due to paused capture or word explaining", interval_seconds)
        
        time.sleep(interval_seconds)


def main():
    book_ui = BookUI()
    thread = threading.Thread(target=gen_loop,args=(book_ui,), daemon = True)
    thread.start()
    book_ui.start_working()
    thread.join()


if __name__ == "__main__":
    main()
    
