
import os, json
from os import environ
from os import path
import requests
from loguru import logger
import uvicorn
from fastapi import FastAPI, Request, File, Form, UploadFile
from fastapi.responses import UJSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import shutil, aiofiles

# from aiofiles import open

deepstack_host_address = 'http://192.168.0.252:5002'
deepstack_api_key = os.getenv("DEEPSTACK_API_KEY")
min_confidence = 0.7

if not min_confidence:
    min_confidence=0.70
else:
    min_confidence=float(min_confidence)

logger.info("#########################################")
logger.info("Deepstack Host Address set to: " + str(deepstack_host_address))
logger.info("Minimum Confidence value set to: " + str(min_confidence))
logger.info("Deepstack api key set to: " + str(deepstack_api_key))

logger.info("#########################################")

def teachme(person,image_file):
    user_image = open(image_file,"rb").read()
    response=""
    if not deepstack_api_key:
        response = requests.post("{}/v1/vision/face/register".format(deepstack_host_address), files={"image1":user_image},data={"userid":person}).json()
    else:
        response = requests.post("{}/v1/vision/face/register".format(deepstack_host_address), files={"image1":user_image},data={"userid":person,"admin_key":"{}}".format(deepstack_api_key)}).json()
    # os.remove(image_file)
    return response

def detection(photo_path):
    image_data = open(photo_path,"rb").read()
    response = requests.post("{}/v1/vision/detection".format(deepstack_host_address),files={"image":image_data}, data={"min_confidence":0.70}).json()
    objects = ""
    for object in response["predictions"]:
        objects = objects + object["label"] + " ,"
    return objects

def detect_scene(photo_path):
    image_data = open(photo_path,"rb").read()
    response = requests.post("{}/v1/vision/scene".format(deepstack_host_address),files={"image":image_data}, data={"min_confidence":0.70}).json()
    return str(response['label'])


def getFaces(photo_path):
    try:
        image_data = open(photo_path,"rb").read()
        response = requests.post("{}/v1/vision/face/recognize".format(deepstack_host_address),files={"image":image_data}, data={"min_confidence":0.70}).json()
        users = ""
        for user in response["predictions"]:
            users = users + user["userid"] + " ,"
        return users
    except Exception as e:
        return str(e)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in "jpg,png,gif,bmp,jpeg"


# app = FastAPI(docs_url="/swagger", openapi_tags=tags_metadata)
app = FastAPI(title="Deepstack Trainer", description="Train your deepstack AI server", version="1.0.0")
app.mount("/dist", StaticFiles(directory="dist"), name="dist")
app.mount("/js", StaticFiles(directory="dist/js"), name="js")
app.mount("/css", StaticFiles(directory="dist/css"), name="css")
app.mount("/img", StaticFiles(directory="dist/img"), name="css")
# app.mount("/plugins", StaticFiles(directory="plugins"), name="plugins")
templates = Jinja2Templates(directory="templates/")



@app.post('/teach')
def teach(person: str = Form(...) ,teach_file: UploadFile = File(...)):
    try:
        if teach_file and allowed_file(teach_file.filename):
            image_file = os.path.join('./', teach_file.filename)
            with open(image_file, "wb") as buffer:
                shutil.copyfileobj(teach_file.file, buffer)
            response = teachme(person,image_file)
            success = str(response['success']).lower()
            if os.path.exists(image_file) and success.lower() == 'false':
                os.remove(image_file)
            if 'message' in str(response):
                message = response['message']
                return JSONResponse(content = '{"message":"'+message+'","success":"'+success+'"}')
            if 'error' in str(response):
                error = response['error']
                return JSONResponse(content = '{"error":"'+error+'","success":"'+success+'"}')
            return response
    except Exception as e:
        error = "Aw Snap! something went wrong"
        return JSONResponse(content = '{"error":"'+error+'","success":"false"}')



@app.post('/who')
def who(who_file: UploadFile = File(...)):
    try:
        if who_file and allowed_file(who_file.filename):
            filename = who_file.filename
            image_file = os.path.join('./', filename)
            with open(image_file, "wb") as buffer:
                shutil.copyfileobj(who_file.file, buffer)
            response = getFaces(image_file)
            if response == '"" ,':
                response='unknown'
            return JSONResponse(content = '{"message":"The person in the picture is ' + str(response) + '","success":"true"}')
    except Exception as e:
        return JSONResponse(content = '{"error":"'+ str(e)  +'","success":"false"}')
    finally:
        if os.path.exists(image_file):
            os.remove(image_file)


@app.post('/detect')
def detect():
    image_file = ""
    if request.method == 'POST':
        if 'detect-file' not in request.files:
            return jsonify('{"error":"No file found in posted data","success":"false"}')
        file = request.files['detect-file']
        if file.filename == '':
            return jsonify('{"error":"File can not be empty","success":"false"}')
        if not allowed_file(file.filename):
            return jsonify('{"error":"File type not supported","success":"false"}')
        try:
            if file and allowed_file(file.filename):
                filename = file.filename
                image_file = os.path.join('./', filename)
                file.save(image_file)
                response = detection(image_file)
                return jsonify('{"message":"The objects in the picture are ' + response + '","success":"true"}')
        except Exception as e:
            return jsonify('{"error":"'+ str(e)  +'","success":"false"}')
        finally:
            if os.path.exists(image_file):
                os.remove(image_file)

@app.post('/scene')
def scene():
    image_file = ""
    if request.method == 'POST':
        # check if the post request has the file part
        if 'scene-file' not in request.files:
            return jsonify('{"error":"No file found in posted data","success":"false"}')
        file = request.files['scene-file']
        if file.filename == '':
            return jsonify('{"error":"File can not be empty","success":"false"}')
        if not allowed_file(file.filename):
            return jsonify('{"error":"File type not supported","success":"false"}')
        try:
            if file and allowed_file(file.filename):
                filename = file.filename
                image_file = os.path.join('./', filename)
                file.save(image_file)
                response = detect_scene(image_file)
                return jsonify('{"message":"The objects in the picture are ' + response + '","success":"true"}')
        except Exception as e:
            return jsonify('{"error":"'+ str(e)  +'","success":"false"}')
        finally:
            if os.path.exists(image_file):
                os.remove(image_file)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse('index.html', context={'request': request})



# Start Application
if __name__ == '__main__':
    uvicorn.run(app)
