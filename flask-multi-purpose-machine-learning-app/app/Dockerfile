FROM python:3.6.6

COPY . /usr/src/app
WORKDIR /usr/src/app

RUN pip install Werkzeug Flask numpy Keras gevent pillow h5py tensorflow python-dotenv stripe SQLAlchemy flask_SQLAlchemy flask_blueprint flask_login


EXPOSE 5000
CMD [ "python" , "app.py"]

