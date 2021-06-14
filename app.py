from flask import Flask, render_template, url_for, request, session, redirect
from pymongo import MongoClient
import bcrypt
import warnings
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from tensorflow.keras.models import model_from_json
from flask_mail import Mail, Message
# import matplotlib.pyplot as plt
import tensorflow

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")

app = Flask(__name__)
mail = Mail(app)
app.secret_key = b'\xba\x89\xd4\\\xc0\x97Ukn\xbc\xf7\xdd\x82\xc99\x80'

url = "mongodb+srv://{}:{}@yourcluster.mongodb.net/majorproject?retryWrites=true&w=majority".format(os.environ['db_username'], os.environ['db_password'])
# database
# database

mongo = MongoClient(url)
print("connection obtained")


# Routes
@app.route('/')
def index():
    login = False
    if 'username' in session:
        login = True
        return render_template('modelpage.html', a=session['username'])
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))
    return 'Invalid username/password '


@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session['logged_in'] = False
    session.pop('username', None)
    return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})
        email_id = users.find_one({'email': request.form['email']})

        if (existing_user or email_id) is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'name': request.form['username'], 'email': request.form['email'], 'password': hashpass})
            session['username'] = request.form['username']

            TEXT = "Hi {} ,Welcome to Leaf Disease Detection App. \n Email-{} \n Password-{}\n The app can be " \
                   "used to detect Leaf disease of tomato, potato and bell pepper".format(request.form['username'],
                                                                                          request.form['email'],
                                                                                          request.form['pass'])
            SUBJECT = "LeafDiseaseDetection"

            app.config['MAIL_SERVER'] = 'smtp.gmail.com'
            app.config['MAIL_PORT'] = 465
            app.config['MAIL_USERNAME'] = "9871pretty@gmail.com"
            app.config['MAIL_PASSWORD'] = os.environ['db_password']
            app.config['MAIL_USE_TLS'] = False
            app.config['MAIL_USE_SSL'] = True
            mail = Mail(app)
            msg = Message(SUBJECT, sender="9871pretty@gmail.com", recipients=request.form['email'].split())
            msg.body = TEXT
            try:
                mail.send(msg)
            except Exception as e:
                return redirect(url_for('index'))


            return redirect(url_for('index'))
        return 'That username or email already exists!'
    return render_template('register.html')


@app.route('/password', methods=['GET', 'POST'])
def password():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})
        if existing_user:
            hashpass = bcrypt.hashpw(request.form['newpass'].encode('utf-8'), bcrypt.gensalt())
            users.update_one({'name': request.form['username']}, {"$set": {'password': hashpass}})
        else:
            return "Not in database"
        return redirect(url_for('index'))

    return render_template('password.html')


@app.route("/train", methods=['POST', 'GET'])
def train():
    """  global model
    model = tensorflow.keras.models.load_model('disease1.h5')"""
    global model
    json_file = open('model.json', 'r')
    model_json = json_file.read()
    json_file.close()
    model = model_from_json(model_json)
    model.load_weights("disease_weights.h5")

    return render_template('loadimage.html')


@app.route("/upload_image", methods=['POST', 'GET'])
def upload_image():
    def prepare(img_path):
        img = image.load_img(img_path, target_size=(256, 256))
        x = image.img_to_array(img)
        x = x / 255

        return np.expand_dims(x, axis=0)

    Classes = ['Pepper__bell___Bacterial_spot', 'Pepper__bell___healthy', 'Potato___Early_blight',
               'Potato___Late_blight', 'Potato___healthy', 'Tomato_Bacterial_spot', 'Tomato_Early_blight',
               'Tomato_Late_blight', 'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
               'Tomato_Spider_mites_Two_spotted_spider_mite', 'Tomato__Target_Spot',
               'Tomato__Tomato_YellowLeaf__Curl_Virus', 'Tomato__Tomato_mosaic_virus', 'Tomato_healthy']
    global model
    json_file = open('model.json', 'r')
    model_json = json_file.read()
    json_file.close()
    model = model_from_json(model_json)
    model.load_weights("disease_weights.h5")
    file = request.files['image']
    file.save(file.filename)
    result = model.predict_classes([prepare(file.filename)])
    disease = image.load_img((file.filename))

    # plt.imshow(disease)
    print(result)
    print(Classes[int(result)])
    return render_template("result.html", message="{}".format(Classes[int(result)]), a=session['username'])


if __name__ == '__main__':
    app.run(debug=True)
