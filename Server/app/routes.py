from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, Response
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, NewTaskForm
from app.models import User, Post, Sensor, Task

import os

import base64

import io

import json 


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    legend = 'Monthly Data'
    labels = ["January", "February", "March", "April", "May", "June", "July", "August"]
    values = [10, 9, 8, 7, 6, 4, 7, 8]
    return render_template('index.html', values=values, labels=labels, legend=legend)


@app.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('events'))
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('events', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('events', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('events.html', title='Events', posts=posts.items,
                           form=form, next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/sensors')
@login_required
def sensors():
    sensors = Sensor.query.all()
    return render_template('sensors.html', title='Sensors', sensors=sensors)

@app.route('/tasks')
@login_required
def tasks():
    tasks = Task.query.all()
    return render_template('tasks.html', title='Tasks', tasks=tasks)

@app.route('/task/<task_id>/<type_data>')
@login_required
def task(task_id, type_data):
    task = Task.query.filter_by(id = task_id).first()
    if type_data == 'screen':
        data = "data:image/jpeg;base64," + base64.b64encode(task.data).decode('utf-8')
    elif type_data == 'shell':
        data = task.data.decode('utf-8')

    return render_template('result.html', 
    title='Result', data = data, type_data = type_data)

@app.route('/new_task', methods=['GET', 'POST'])
def new_task():
    form = NewTaskForm()
    if form.validate_on_submit():

        bytes_file = None

        if form.data.data != None:
            bytes_file = form.data.data.read()
        task = Task(cmd = form.cmd.data, type=form.type.data, 
        data=bytes_file,
        flag_wait_result=form.flag_wait_result.data,
        status='waiting',
        sensor_id=form.sensor_id.data)

        db.session.add(task)
        db.session.commit()
        flash('A new task has been added to the queue.')
        return redirect(url_for('tasks'))
    return render_template('new_task.html', title='New Task', form=form)


@app.route('/upload/<machine_id>/<task_id>', methods=['POST'])
def upload_file(machine_id, task_id):

    message = json.loads(request.json)
    try:
        information = json.loads(message['data'])
    except:
        pass
    if message['cmd_type'] == 'collect info':
        update_sensor_info(machine_id, information)
        message['data'] = None
        
    if  message['cmd_type'] == 'init':
        message['data'] = None
        if bool(Sensor.query.filter_by(id = machine_id).first()) == False:
            sensor = Sensor(id = machine_id, OS = information['OS'], 
                domain = information['domain'], 
                workgroup = information['workgroup'], hostname = information['hostname'], 
                username = information['current_username'], version = information['version'],
                language = information['language'], UUID = information['UUID'], 
                current_time = information['current_time'], timezone = information['timezone'], 
                boot_time = information['boot_time'], machineinfo = information)
            db.session.add(sensor)

            task = Task(type = message['cmd_type'], cmd = message['cmd'],
                time_result = datetime.strptime(message['time_result'], '%Y-%m-%d %H-%M-%S'),
                data = message['data'], status = message['status'], 
                flag_wait_result = message['flag_wait_result'], sensor_id = machine_id)
            db.session.add(task)
    elif message['cmd_type'] != 'standby':
        if message['data'] != None:
            encoded_string = message['data'].encode('utf-8')
            message['data'] = base64.b64decode(encoded_string)
        task = Task.query.filter_by(id = task_id).first()
        task.time_result = datetime.strptime(message['time_result'], '%Y-%m-%d %H-%M-%S')
        task.data = message['data']
        task.status = message['status']

    db.session.commit()
    answer = None
    waiting_task = Task.query.filter_by(sensor_id = machine_id, status='waiting').first()
    if waiting_task != None:
        decode_data = None
        if waiting_task.data != None:
            decode_data = base64.b64encode(waiting_task.data).decode('utf-8')
        task = {"cmd_id": waiting_task.id, "cmd": waiting_task.cmd,
         "cmd_type": waiting_task.type, "time_limit": 0,
         "data": decode_data, 
         "flag_wait_result": waiting_task.flag_wait_result}
    else:
        task = {"cmd_id": None, "cmd": None,
         "cmd_type": 'standby', "time_limit": 60, "data": None, "flag_wait_result": True}
    answer = json.dumps(task, default=lambda o: o.__dict__)
    return Response(response = answer, status = 200)

def update_sensor_info(machine_id, information):
    sensor = Sensor.query.filter_by(id = machine_id).first()
    sensor.OS = information['OS']
    sensor.domain = information['domain']
    sensor.workgroup = information['workgroup']
    sensor.hostname = information['hostname']
    sensor.username = information['current_username']
    sensor.version = information['version']
    sensor.language = information['language']
    sensor.UUID = information['UUID']
    sensor.current_time = information['current_time']
    sensor.timezone = information['timezone']
    sensor.boot_time = information['boot_time']
    sensor.machineinfo = information

@app.route('/sensor/<sensor_id>/<type_info>')
@login_required
def info(sensor_id, type_info):
    sensor = Sensor.query.filter_by(id = sensor_id).first()
    data = sensor.machineinfo[type_info]
    return render_template('/info/' + type_info + '.html', title='Info', data = data)