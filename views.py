import subprocess
import os
import sys
import random
from skimage import io
from werkzeug.utils import secure_filename
from flask import render_template
from flask import send_from_directory
from flask import Flask, request, redirect, url_for
from app import app


here = os.getcwd()
UPLOAD_FOLDER = here + '/static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'JPG', 'JPEG'}
TEMP = "temp"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(64)


def glitch_it(input_image, params):
    temp_name = str(random.randint(1000000, 9999999)) + '.jpg'
    temp_path = os.path.join(TEMP, temp_name)
    glitch_cmd = "{0} main.py {1} {2}".format(sys.executable, input_image, temp_path)
    # add params if required
    glitch_cmd = glitch_cmd + " -g {0}".format(params["gamma"]) if params["gamma"] else glitch_cmd
    glitch_cmd = glitch_cmd + " -b {0}".format(params["blue_red"]) if params["blue_red"] else glitch_cmd
    glitch_cmd = glitch_cmd + " -l {0}".format(params["blacks"]) if params["blacks"] else glitch_cmd
    glitch_cmd = glitch_cmd + " -r {0}".format(params["whites"]) if params["whites"] else glitch_cmd

    rc = subprocess.call(glitch_cmd, shell=True)
    print(glitch_cmd)
    if rc != 0:
        print('FATALITY')
    out = io.imread(temp_path)
    return out


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def is_float(num):
    try:  # I didnt find any beaty way to do that
        num = float(num)
        return True
    except ValueError:
        return False


def make_params(blue_red_raw, gamma_raw, blacks_raw, whites_raw):
    """Return params dict for glitcher."""
    # read black_red
    blue_red = None if len(blue_red_raw) == 0 or not blue_red_raw.isdigit() else (int(blue_red_raw) // 2) * 2
    blue_red = None if blue_red and blue_red < 0 else blue_red  # it happens
    # read gamma
    gamma = None if len(gamma_raw) == 0 or not is_float(gamma_raw) else float(gamma_raw)
    gamma = None if gamma and gamma < 0 else gamma  # if any user will
    # read blacks
    blacks = None if len(blacks_raw) == 0 or not blacks_raw.isdigit() else int(blacks_raw)
    blacks = None if blacks and blacks < 0 else blacks
    # and whites
    whites = None if len(whites_raw) == 0 or not whites_raw.isdigit() else int(whites_raw)
    whites = None if whites and whites < 0 else whites
    return {"blue_red": blue_red, "gamma": gamma, "blacks": blacks, "whites": whites}


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            # get file and save it
            filename = secure_filename(file.filename)
            in_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # also extract params from form
            blue_red_raw = request.form['blue_red_shift']
            gamma_raw = request.form['gamma']
            blacks_raw = request.form["blacks"]
            whites_wites = request.form["whites"]
            params = make_params(blue_red_raw, gamma_raw, blacks_raw, whites_wites)
            file.save(in_file)
            # glitch the image
            glim = glitch_it(in_file, params)
            # save in the same folder
            io.imsave(in_file, glim)

            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return render_template('start_page.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
