import subprocess
import os
import sys
import random
import string
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


def id_gen(size=12, chars=string.ascii_uppercase + string.digits):
    """Return random string for temp files."""
    return "".join(random.choice(chars) for _ in range(size))


def glitch_it(input_image, params, checkbox):
    # temp_name = id_gen() + '.jpg'
    # temp_path = os.path.join(TEMP, temp_name)
    glitch_cmd = "{0} gleitzsch.py {1} {2}".format("python3", input_image, input_image)
    # add params if required
    glitch_cmd = glitch_cmd + " -b {}".format(params["blue_red"]) if params["blue_red"] else glitch_cmd
    glitch_cmd = glitch_cmd + " --text \"{}\"".format(params["text"]) if params["text"] else glitch_cmd

    glitch_cmd = glitch_cmd + " --hor_shifts" if checkbox["hp"] else glitch_cmd
    glitch_cmd = glitch_cmd + " --v_streaks" if checkbox["smudges"] else glitch_cmd
    glitch_cmd = glitch_cmd + " --rainbow" if checkbox["rainbow"] else glitch_cmd
    glitch_cmd = glitch_cmd + " --glitter" if checkbox["glitter"] else glitch_cmd
    glitch_cmd = glitch_cmd + " --interlacing" if checkbox["interlacing"] else glitch_cmd
    glitch_cmd = glitch_cmd + " --figures" if checkbox["crimson"] else glitch_cmd
    glitch_cmd = glitch_cmd + " --bitrate 12" if checkbox["bitrate"] else glitch_cmd

    rc = subprocess.call(glitch_cmd, shell=True)
    print(glitch_cmd)
    if rc != 0:
        print('FATALITY')
    # out = io.imread(temp_path)
    # os.remove(temp_path)
    # return out


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def is_float(num):
    try:  # I didnt find any beaty way to do that
        num = float(num)
        return True
    except ValueError:
        return False


def make_text_params(text_params):
    """Return params dict for glitcher."""
    # read black_red
    blue_red = None if len(text_params["blue_red_raw"]) == 0 or not text_params["blue_red_raw"].isdigit() \
        else (int(text_params["blue_red_raw"]) // 2) * 2
    blue_red = None if blue_red and blue_red < 0 else blue_red  # it happens
    # text option
    text = None if len(text_params["text"]) == 0 else str(text_params["text"])
    gleitzsch_params = {"blue_red": blue_red,
                        "text": text}
    return gleitzsch_params


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            # get file and save it
            filename = secure_filename(file.filename)
            in_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            # also extract params from form
            text_params, checkboxes = dict(), dict()
            text_params["blue_red_raw"] = request.form["blue_red_shift"]
            text_params["text"] = request.form["text"]

            checkboxes["hp"] = True if request.form.getlist("hp") else False
            checkboxes["smudges"] = True if request.form.getlist("smudges") else False
            checkboxes["rainbow"] = True if request.form.getlist("rainbow") else False
            checkboxes["glitter"] = True if request.form.getlist("glitter") else False
            checkboxes["interlacing"] = True if request.form.getlist("interlacing") else False
            checkboxes["crimson"] = True if request.form.getlist("crimson") else False
            checkboxes["bitrate"] = True if request.form.getlist("bitrate") else False

            params = make_text_params(text_params)
            file.save(in_file)
            # glitch the image
            glitch_it(in_file, params, checkboxes)
            # save in the same folder
            # io.imsave(in_file, glim)

            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return render_template('start_page.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
