from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
import cv2
import pickle
import struct
from time import sleep
import CarDriver

LAPTOP_IP = '10.42.0.134'
IMAGE_STREAMING_PORT = 2003
DRIVING_STATUS_STREAMING_PORT = 2004
STREAMING_IMAGE_WIDTH = 320
STREAMING_IMAGE_HEIGHT = 240

image_streaming_socket = socket(AF_INET, SOCK_STREAM)
driving_status_socket = socket(AF_INET, SOCK_STREAM)

shutdown = False
framerate = 20

status_list = ['stop']

def intialize_and_start_streaming():
    initialize()
    start_streaming()

def initialize():
    image_streaming_socket.connect((LAPTOP_IP, IMAGE_STREAMING_PORT))
    driving_status_socket.connect((LAPTOP_IP, DRIVING_STATUS_STREAMING_PORT))
    
def start_streaming():    
    camera = cv2.VideoCapture(0)
    camera.set(3, STREAMING_IMAGE_WIDTH)
    camera.set(4, STREAMING_IMAGE_HEIGHT)
    
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    
    while not shutdown:
        _, frame = camera.read()
        _, frame = cv2.imencode('.jpg', frame, encode_param)
        # convert the captured image as binary
        data = pickle.dumps(frame, 0)
        size = len(data)
        
        # send the byte stream length followed by the byte stream representing the image
        image_streaming_socket.sendall(struct.pack(">L", size) + data)
        
        # wait for the server to acknowledge the image receival 
        driving_status_socket.recv(1024)
        
        message = status_list[0]
        driving_status_socket.sendall(message.encode())
        
        # wait for the server to acknowledge the receival of the driving status
        driving_status_socket.recv(1024)
        
        sleep(1/framerate)

    camera.release()
    print("Stopping streaming.")
    
def send_single_frame(image_frame):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    _, frame = cv2.imencode('.jpg', image_frame, encode_param)
    # convert the captured image as binary
    data = pickle.dumps(frame, 0)
    size = len(data)
    
    # send the byte stream length followed by the byte stream representing the image
    image_streaming_socket.sendall(struct.pack(">L", size) + data)
    
    # wait for the server to acknowledge the image receival 
    driving_status_socket.recv(1024)
    
    message = status_list[0]
    driving_status_socket.sendall(message.encode())
    
    # wait for the server to acknowledge the receival of the driving status
    driving_status_socket.recv(1024)

def force_shutdown():
    global shutdown
    image_streaming_socket.shutdown(SHUT_RDWR)
    driving_status_socket.shutdown(SHUT_RDWR)
    image_streaming_socket.close()
    driving_status_socket.close()
    shutdown = True
    print("Closed streaming servers.")
    
def run_status_buffering():
    while not shutdown:
        if len(status_list) > 3:
            del status_list[0]
        status_list.append(CarDriver.current_driving_status)
        sleep(0.055)
    print("Stopped driving status buffering.")
        
     
