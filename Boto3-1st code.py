import boto3
import csv

# Read AWS credentials from CSV file
with open('credentials.csv', 'r') as file:
    next(file)
    reader = csv.reader(file)
    for line in reader:
        access_key_id = line[0]
        secret_access_key = line[1]

# Create Boto3 client for Rekognition
try:
    client = boto3.client('rekognition', region_name='us-east-2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)

    # Specify the image file
    photo = 'image.jpeg'

    # Open the image file in binary mode
    with open(photo, 'rb') as image:
        source_bytes = image.read()

    # Perform object detection
    detect_object = client.detect_labels(Image={'Bytes': source_bytes})

    # Print the result
    print(detect_object)

except Exception as e:
    print(f"Error: {e}")
