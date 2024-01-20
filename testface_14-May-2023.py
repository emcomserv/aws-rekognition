import cv2
import sys
import time
import os
from datetime import datetime
import tarfile
import boto3
import RPi.GPIO as GPIO
import time
from senddata import send_email_to_destination
import pymysql
import pymysql.cursors
import uuid  # Import the UUID module
from datetime import datetime  # Import the datetime module
from config import *  # Import parameters for PyMySQL connection e.g. ENDPOINT, PORT, etc.

while True:
  faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
  #eyeCascade  = cv2.CascadeClassifier('haarcascade_eye.xml')
  eyeCascade=cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
  cv2.namedWindow("preview")
  vc = cv2.VideoCapture(0)
  email_password = os.environ.get("EMAIL_PASS")
  fromaddr = 'ramachandrar914@gmail.com'
  toaddr = 'ramachandrar914@gmail.com'
  
  # Set the Row Pins
  RED_Button = 16
  Blue_Button = 20
  
  LIGHT_SW=22
  FAN_SW=23
  TV_SW=24
  AC_SW=25
  
  SendToS3 = 'N'
  
  GPIO.setwarnings(False)
  # BCM numbering
  GPIO.setmode(GPIO.BCM)
  
  # Set column pins as input and Pulled up high by default
  GPIO.setup(RED_Button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(Blue_Button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  
  GPIO.setup(LIGHT_SW, GPIO.OUT)
  GPIO.setup(FAN_SW, GPIO.OUT)
  GPIO.setup(TV_SW, GPIO.OUT)
  GPIO.setup(AC_SW, GPIO.OUT)
  
  GPIO.output(LIGHT_SW, GPIO.HIGH)
  GPIO.output(FAN_SW, GPIO.HIGH)
  GPIO.output(TV_SW, GPIO.HIGH)
  GPIO.output(AC_SW, GPIO.HIGH)
  # We need to check if camera
  # is opened previously or not
  if (vc.isOpened() == False): 
      print("Error reading video file")
      
  # We need to set resolutions.
  # so, convert them from float to integer.
  frame_width = int(vc.get(3))
  frame_height = int(vc.get(4))
     
  size = (frame_width, frame_height)
     
  # Below VideoWriter object will create
  # a frame of above defined The output 
  # is stored in 'filename.avi' file.
    
  
  thresholdtime=int(60)
  loopcount=int(0)
  while loopcount < 1:
    timestr = time.strftime("%Y%m%d-%H%M%S");
    tarfilename='video_'+timestr+'.tar.xz'
    filename='video_'+timestr+'.avi'
    #result = cv2.VideoWriter('filename.avi', cv2.VideoWriter_fourcc(*'MJPG'), 10, size)
    result = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'MJPG'), 10, size)
        
    start = abs(time.time())
    print("Start time is ", start)
    elapsedtime = 0
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
  
    while True: # try to get the first frame
        rval, frame = vc.read()
        # Capture frame-by-frame
        ret, frame = vc.read()
        
        #Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.2, 
                                               minNeighbors=1, minSize=(40, 40), 
                                               flags=cv2.CASCADE_SCALE_IMAGE)
        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            #select face as region of interest 
            roi_g =  gray[y:y+h,x:x+h]
            roi_c = frame[y:y+h,x:x+h]
            #within region of interest find eyes
            #eyes = eyeCascade.detectMultiScale(roi_g)
            #for each eye
            #for (ex,ey,ew,eh) in eyes:
            #    #draw retangle around eye
            #    cv2.rectangle(roi_c, (ex,ey),(ex+ew,ey+eh),(0,255,0),2)
                    
        cv2.imshow("preview", frame)
        
         # Write the frame into the
            # file 'filename.avi'
        result.write(frame)
      
            # Display the frame
            # saved in the file
        cv2.imshow('Frame', frame)
        cv2.imwrite('messigray.png',frame)
        
        end = abs(time.time())
        print("End time is ", end)
        elapsedtime=abs(end)-abs(start)
        print("Elapsed Time :",elapsedtime)
        
        if(GPIO.input(RED_Button) == GPIO.LOW) or (GPIO.input(Blue_Button) == GPIO.LOW):
          SendToS3 = 'Y'
          print("Button is Pressed\r\n")          
        
        if(GPIO.input(RED_Button) == GPIO.LOW):
          #GPIO.output(LIGHT_SW, GPIO.LOW)
          GPIO.output(FAN_SW, GPIO.LOW)
        
        if(GPIO.input(Blue_Button) == GPIO.LOW):
          #GPIO.output(TV_SW, GPIO.LOW)
          GPIO.output(AC_SW, GPIO.LOW)
          
        if (elapsedtime > 5) and ((elapsedtime > thresholdtime) or (SendToS3 == 'Y')):
          loopcount=loopcount+1
          SendToS3 = 'N'
          #declaring the filename
          file_stats = os.stat(filename)
          
          print(file_stats)
          
          SizeOfFile= file_stats.st_size
          
          print("File Size to be send:",SizeOfFile)
  
          name_of_file= "TutorialsPoint.tar"
          
          #opening the file in write mode
          file= tarfile.open(tarfilename,"w:xz")
          
          #Adding other files to the tar file
          file.add(filename)
          
          #file.add("trial.py")
          #file.add("Programs.txt")
                  
          #closing the file
          file.close()  
          
          print("Video Elapsed Time is greater than Threshold")
          #send_email_to_destination(fromaddr, toaddr, tarfilename, email_password)
          #add code below for sending data to S3 bucket
          s3=boto3.client('s3')
          #s3.upload_file(r'/home/admin123/object/video_20231027-091437.avi', 'emcom1', 'video.avi')
          s3.upload_file(tarfilename, 'emcom1',tarfilename)
          print("Email with attachement is sent",tarfilename)
          
          #add entries to database
          GPIO.output(LIGHT_SW, GPIO.HIGH)
          GPIO.output(FAN_SW, GPIO.HIGH)
          GPIO.output(TV_SW, GPIO.HIGH)
          GPIO.output(AC_SW, GPIO.HIGH)
          
          USERNAME = 'admin'
          PASSWORD = 'admin123'
          ENDPOINT = "emcom.c0c6xz0ndvmf.ap-south-1.rds.amazonaws.com"
          PORT = 3306
          REGION = "ap-south-1"
          DBNAME = 'schema1'
          SSL_CA = "/home/admin123/rds-combined-ca-bundle.pem"
          CURSORCLASS = pymysql.cursors.DictCursor
  
          def start_rds_connection():
              try:
                  connection = pymysql.connect(host=ENDPOINT,
                                               port=PORT,
                                               user=USERNAME,
                                               passwd=PASSWORD,
                                               db=DBNAME,
                                               cursorclass=CURSORCLASS,
                                               ssl_ca=SSL_CA)
                  print('[+] RDS Connection Successful')
              except Exception as e:
                  print(f'[+] RDS Connection Failed: {e}')
                  connection = None
          
              return connection
          
          # Initiate RDS connection
          connection = start_rds_connection()
          
          def extract_file_type(file_name):
              # Extract file type from file name or extension
              # Example: if file_name is "example.txt", file_type will be "txt"
              file_type = file_name.split('.')[-1].lower()
              return file_type
          
          def insert_record():
              tableName = 'emcom'
              Name = tarfilename
              Size = SizeOfFile
              Location = input("Enter Location (format: 'latitude longitude'): ")
          
              # Generate a unique ID using UUID
              ID = str(uuid.uuid4())
          
              # Automatically extract file type from file name or extension
              FileType = extract_file_type(Name)
          
              TimeStamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp
          
              try:
                  with connection.cursor() as cursor:
                      sql = f"INSERT INTO `{tableName}` (`ID`, `FileType`, `Name`, `Size`, `TimeStamp`, `Location`) VALUES (%s, %s, %s, %s, %s, %s)"
                      cursor.execute(sql, (ID, FileType, Name, Size, TimeStamp, Location))
          
                  # Connection is not autocommit by default, so we must commit to save changes
                  connection.commit()
                  print(f'Successfully inserted record into {tableName}')
              except Exception as e:
                  print(f'Error in insertion to MySQL database: {e}')
          
          # Execute record insertion
          insert_record()
          
          # Display the inserted records
         # with connection.cursor() as cursor:
          #    sql = f"SELECT * FROM `emcom`"
           #   cursor.execute(sql)
            #  result = cursor.fetchall()  # Retrieve all rows
             # print(result)
          
          # Close the connection
          connection.close()
          break
    
        rval, frame = vc.read()
        key = cv2.waitKey(20)
        if key == 27: # exit on ESC
            loopcount=loopcount+1
            break
  
  vc.release()
  cv2.destroyWindow("preview")
  # When everything done, release 
  # the video capture and video 
  # write objects
  
  result.release()
      
  # Closes all the frames
  cv2.destroyAllWindows()
     
  print("The video was successfully saved") 

