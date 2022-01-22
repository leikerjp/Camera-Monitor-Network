import requests
import numpy
import cv2
import time
import json


def load_client_settings(path):
    # Opening JSON file
    with open(path, 'r') as json_file:
        # Read file object into dict
        client_settings = json.load(json_file)

    return client_settings


def setup_camera(camera_handle, camera_settings):

    # Create capture device
    cam = cv2.VideoCapture(camera_handle)

    # Setup capture device
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, camera_settings['width'])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_settings['height'])
    cam.set(cv2.CAP_PROP_FPS, camera_settings['framerate'])

    return cam


if __name__ == "__main__":

    # Initialize camera
    client_settings = load_client_settings('settings.json')
    camera = setup_camera(0, client_settings['camera_settings'])
    if not camera.isOpened():
        exit("Camera Failed to Open - Exiting")


    # The 'simple client' does captures every 5 seconds.
    time_to_wait_in_seconds = 5
    previous_time_in_seconds = 0
    current_time_in_seconds = time.time()


    while True:

        # Read a frame and resize (size was arbitrarily picked)
        ret, frame = camera.read()
        if not ret:
            print("Empty Frame Failure - Exiting")
            break;

        # Calculate elapsed time since last sent message, we only want to send if time has been
        # great than 5 seconds.
        time_elapsed = current_time_in_seconds - previous_time_in_seconds > time_to_wait_in_seconds

        if time_elapsed:

            # Serialize the image in preparation to send over REST API
            imencoded = cv2.imencode(".jpg", frame)[1]
            data_encode = numpy.array(imencoded).tobytes()
            file = dict(file=('image.jpg', data_encode, 'image/jpeg', {'Expires': '0'}))

            # Send to server
            client_metadata = dict(id=client_settings['id'], name=client_settings['name'])
            response = requests.post('http://192.168.0.122:5000/log_image', files=file, data=client_metadata)

            # If we get a response it's to update our camera's id because
            # this is the first time we sent a message
            if response.content:
                respDict = response.json()
                client_settings['id'] = respDict['id']

                # Update the settings with the server provided ID.
                with open('settings.json', 'w') as outfile:
                    json.dump(client_settings, outfile)

            # Update previous time (because we just did a send)
            previous_time_in_seconds = current_time_in_seconds

        # The last thing in the loop is to update the current time for the elapsed time calculation
        current_time_in_seconds = time.time()


    # When everything done, release the capture (though we really won't get here)
    camera.release()
    cv2.destroyAllWindows()
