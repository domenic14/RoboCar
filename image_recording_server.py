# Code from https://gist.github.com/kittinan/e7ecefddda5616eab2765fdb2affed1b
# slightly edited by myself to save images
import socket
import cv2
import pickle
import numpy as np
import struct
from datetime import datetime
import signal
from pynput import keyboard
import os

IMAGE_BASE_PATH=os.getcwd()+ "\\images\\"
IMAGE_PATH = IMAGE_BASE_PATH + datetime.now().strftime('%Y%m%d_%H%M%S')
driving_status_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
image_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
image_id = 0
close_connection = False
record = False
dataset_dir_created = False

def create_dataset_directory():
    global dataset_dir_created
    if not dataset_dir_created:
        os.mkdir(IMAGE_PATH)
        dataset_dir_created = True

def setup_sockets():
    print("Setting image socket up...")
    image_socket.bind(('',2003))
    image_socket.listen()

    print("Setting driving status socket up...")
    driving_status_socket.bind(('', 2004))
    driving_status_socket.listen()

def signal_handler(sig, frame):
    global close_connection
    close_connection = True
    image_socket.shutdown(socket.SHUT_RDWR)
    image_socket.close()
    driving_status_socket.shutdown(socket.SHUT_RDWR)
    driving_status_socket.close()

def on_press(key):
    global record
    global close_connection
    if key == keyboard.Key.space:
        record = not record
    elif key == keyboard.Key.esc:
        close_connection = True
        image_socket.shutdown(socket.SHUT_RDWR)
        image_socket.close()
        driving_status_socket.shutdown(socket.SHUT_RDWR)
        driving_status_socket.close()
        return False    # stop the key listener

signal.signal(signal.SIGINT, signal_handler)    
listener = keyboard.Listener(on_press=on_press)
listener.start()
setup_sockets()

print('Image socket now accepting...')
image_retrieval_connection, _ = image_socket.accept()

print("Driving status socket now accepting...")
driving_status_connection, _ = driving_status_socket.accept()

# config for displaying the driving status on the image
font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfDrivingStatusLabel = (10,50)
bottomLeftCornerOfRecordingLabel = (10,80)
fontScale              = 1
fontColor              = (255,255,255)
thickness              = 1
lineType               = 2

data = b""
payload_size = struct.calcsize(">L")

while not close_connection:
    data = b""
    
    while len(data) < payload_size:
        data += image_retrieval_connection.recv(4096)
        
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    
    while len(data) < msg_size:
        data += image_retrieval_connection.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]
    frame= pickle.loads(frame_data, fix_imports=True, encoding="bytes")
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    
    # show the client that we area ready for receiving the driving status
    driving_status_connection.sendall("ack".encode())
    
    # get the driving status
    drivingStatus = driving_status_connection.recv(1024).decode()
    print("Current driving status: ", drivingStatus)
    
    # send acknowledgement that we received the driving status
    driving_status_connection.sendall("ack".encode())
    
    if record:
        create_dataset_directory()
        image_name = IMAGE_PATH + '\\' + datetime.now().strftime('%Y%m%d_%H%M%S') + "_" + "{:04d}".format(image_id) + "_" + drivingStatus + ".jpg"
        cv2.imwrite(image_name, frame)
        cv2.putText(frame, "recording", bottomLeftCornerOfRecordingLabel, font, fontScale, fontColor, thickness, lineType)
        image_id += 1
        image_id = image_id % 1000  # don't let it get too high
    
    cv2.putText(frame, drivingStatus, bottomLeftCornerOfDrivingStatusLabel, font, fontScale, fontColor, thickness, lineType)

    cv2.imshow('ImageWindow',frame)
    cv2.waitKey(1)

print("Closing listener...")
listener.join()
print("Closing image socket...")
image_socket.close()
print("Closing driving status socket...")
driving_status_socket.close()
