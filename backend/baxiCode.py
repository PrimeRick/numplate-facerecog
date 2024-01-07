import firebase_admin
from firebase_admin import credentials, storage, db
# import face_recognition
from utils import final_processed, OCR_results, download_image_from_storage,Validation_img
from roboflow import Roboflow
import os
import cv2
from ultralytics import YOLO


cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'numplate-face.appspot.com',
                                     'databaseURL': 'https://numplate-face-default-rtdb.firebaseio.com/'})

# rf = Roboflow(api_key="ULr8zI3pE4MU4eijDqFm")
# project = rf.workspace().project("license-plate-detection-l8xs4")
# model = project.version(1).model
# from roboflow import Roboflow
# rf = Roboflow(api_key="HhAXwGi82YEUEVgbOWBP")
# project = rf.workspace().project("lincence-plate-detction")
# model = project.version(1).model
from sort.sort import *
# infer on a local image
# print(model.predict("your_image.jpg", confidence=40, overlap=30).json())
# visualize your prediction
# model.predict("your_image.jpg", confidence=40, overlap=30).save("prediction.jpg")
# infer on an image hosted elsewhere
# print(model.predict("URL_OF_YOUR_IMAGE", hosted=True, confidence=40, overlap=30).json())
coco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO('weights/best.pt')
ref = db.reference('num-face')

def Validation(UpfileName):

    download_image_from_storage(UpfileName, 'test.mp4')

    picture = "test.png"
    # image = cv2.imread(picture)
    # infer on a local image
    cap = cv2.VideoCapture('./test.mp4')

    # detections = model.predict(picture, confidence=40, overlap=30).json()

    vehicles = [2, 3, 5, 7]
    # model.predict(picture, confidence=20, overlap=30).save("backend/prediction.jpg")

    # print(detections)
    frame_nmr = -1
    ret = True
    while ret:
        frame_nmr += 1
        ret, frame = cap.read()

        if ret:
            # for prediction in detections['predictions']:
            #     x1 = float(prediction['x']) - float(prediction['width']) / 2
            #     x2 = float(prediction['x']) + float(prediction['width']) / 2
            #     y1 = float(prediction['y']) - float(prediction['height']) / 2
            #     y2 = float(prediction['y']) + float(prediction['height']) / 2
            #     class_id = prediction['class_id']
            #     score = prediction['confidence']
            #     # box = (x1, y1, x2, y2)
            #     x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            detections = coco_model(frame)[0]
            detections_ = []
            for detection in detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = detection
                if int(class_id) in vehicles:
                    detections_.append([int(x1), int(y1), int(x2), int(y2), score])


            license_plates = license_plate_detector(frame)[0]
            for license_plate in license_plates.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = license_plate
                print(f"hey  {license_plate} hi here is outhput")
                if(class_id==0):
                    detection_crop =frame[int(y1):int(y2), int(x1):int(x2), :]
                    fin_processed = final_processed(detection_crop)
                    filename = f'x1_{x1}.jpg'
                #
                    output_path = os.path.join('output_images', filename)
                    cv2.imwrite(output_path, fin_processed)
                    ocr_texts = Validation_img(fin_processed)
                    print(ocr_texts)
                    ocr_text_string = ' '.join(map(str, ocr_texts))

                    print("The license plate number is:", ocr_text_string)

                    # Create a unique filename based on OCR text or x1 coordinate
                    if ocr_texts:
                        fileName = f'{ocr_text_string}.jpg'
                    #
                    # # Save the fin_processed image
                    output_Path = os.path.join('output_images', fileName)
                    cv2.imwrite(output_Path, detection_crop)

                    os.remove(output_path)

                    # Function to find a match and return the ID and name
                    def find_match(input_licence):
                        data = ref.get()
                        for key, value in data.items():
                            if value.get('licence') and value.get('licence') in input_licence:
                                return key, value.get('name')
                        return None, None

                    # Example usage
                    result_id, result_name = find_match(ocr_text_string)

                    if result_id is not None:
                        # download_image_from_storage('Registration/' + result_id, 'validating.png')
                        # 
                        # validation_image = face_recognition.load_image_file("validating.png")
                        # original_image = face_recognition.load_image_file(picture)
                        # try:
                        #     validation_image_encoding = face_recognition.face_encodings(validation_image)[0]
                        #     original_image_encoding = face_recognition.face_encodings(original_image)[0]
                        #     results = face_recognition.compare_faces([validation_image_encoding], original_image_encoding)
                        #     print(results)
                        # except IndexError:
                        #     print("I wasn't able to locate any faces in at least one of the images. Check the image files. Aborting...")
                        #     quit()
                        # os.remove('test.png')
                        # os.remove('validating.png')
                        # if(results[0]==True):
                        #     print(f"Match found! ID: {result_id}, Name: {result_name} and Faces matches also found")
                        #     return (result_name,results[0])
                        return(result_name)
                    else:
                        return("No match found.")