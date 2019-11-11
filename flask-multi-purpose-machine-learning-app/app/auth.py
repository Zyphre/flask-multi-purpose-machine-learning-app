# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required,UserMixin
from .models import User
from . import db
from flask import Flask, render_template, request, redirect, url_for,Response
import stripe
import numpy as np
from sklearn import *
import pickle

import sys
import os
import glob
import re

from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

# Keras
from tensorflow.keras.applications.imagenet_utils import preprocess_input, decode_predictions
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image


# testing
from .camera import VideoCamera
# import cv2
# from flask import Flask, render_template, Response, jsonify
# from .camera import VideoCamera


app = Flask(__name__)

# video_stream = VideoCamera()

# @app.route('/')
# def index():
#     return render_template('index.html')

#     def gen(camera):
#         while True:
#             frame = camera.get_frame()
#             yield (b'--frame\r\n'
#                 b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# @app.route('/video_feed')
# def video_feed():
#     return Response(gen(video_stream),
#                 mimetype='multipart/x-mixed-replace; boundary=frame')


# users = {'foo@bar.tld': {'password': 'secret'}}

# class User(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
#     email = db.Column(db.String(100), unique=True)
#     password = db.Column(db.String(100))
#     name = db.Column(db.String(1000))

app = Flask(__name__)


pub_key = 'pk_test_GfV4kl0nfS6Eb8Wr0sBOPMss009QCCHLpN'
secret_key = 'sk_test_gIz6GEr5lWI18DfYySMEhJDc00J6cpbSaV'

stripe.api_key = secret_key


# Model saved with Keras model.save()
# MODEL_PATH = 'models/yolo3-tiny.h5'

# You can also use pretrained model from Keras
# Check https://keras.io/applications/

from tensorflow.keras.applications.resnet50 import ResNet50
model = ResNet50(weights='imagenet')
# from tensorflow.keras.applications.Resnet50V2
# model = 
print('Model loaded. Check http://127.0.0.1:5000/')

# predict function
def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(224, 224))

    # Preprocessing the image
    x = image.img_to_array(img)
    # x = np.true_divide(x, 255)
    x = np.expand_dims(x, axis=0)

    # Be careful how your trained model deals with the input
    # otherwise, it won't make correct prediction!
    x = preprocess_input(x, mode='caffe')

    preds = model.predict(x)
    return preds


# @app.route('/predict', methods=['GET', 'POST'])
# def upload():
#     if request.method == 'POST':
#         # Get the file from post request
#         f = request.files['image']

#         # Save the file to ./uploads
#         basepath = os.path.dirname(__file__)
#         file_path = os.path.join(
#             basepath, 'uploads', secure_filename(f.filename))
#         f.save(file_path)

#         # Make prediction
#         preds = model_predict(file_path, model)

#         # Process your result for human
#         # pred_class = preds.argmax(axis=-1)            # Simple argmax
#         pred_class = decode_predictions(preds, top=1)   # ImageNet Decode
#         result = str(pred_class[0][0][1])               # Convert to string
#         return result
#     return None
# 
# 
auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

# expression recognition block
@auth.route('/face')
def face():
    return(render_template('face.html'))

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@auth.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
# end expression recognition block

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/profile')
@login_required
def index():
    return render_template('profile.html', pub_key=pub_key)

@auth.route('/thanks')
@login_required
def thanks():
    return render_template('thanks.html', result="")

@auth.route('/pay', methods=['POST'])
def pay():

    customer = stripe.Customer.create(email=request.form['stripeEmail'], source=request.form['stripeToken'])

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=69,
        currency='usd',
        description='Competitive purrices! Whatcha got to lose?'
    )

    return redirect(url_for('auth.thanks'))

if __name__ == '__main__':
    auth.run(debug=True)

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():

    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))


@auth.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['image']

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)

        # Make prediction
        preds = model_predict(file_path, model)

        # Process your result for human
        # pred_class = preds.argmax(axis=-1)            # Simple argmax
        pred_class = decode_predictions(preds, top=1)   # ImageNet Decode
        result = str(pred_class[0][0][1])               # Convert to string
        return result
    return None


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))



   