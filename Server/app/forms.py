from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField, IntegerField, TimeField
from flask_wtf.file import FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from app.models import User, Sensor, Task
import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class PostForm(FlaskForm):
    post = TextAreaField('What happened?', validators=[DataRequired()])
    submit = SubmitField('Submit')

class NewTaskForm(FlaskForm):
    sensor_id = SelectField('Sensor ID', coerce = int, choices = [(c.id, c.hostname) for c in Sensor.query.all()])
    type = SelectField('Type', choices = [('collect info', 'Collectiong System Information'), 
    ('save file', 'Save File From Server'), ('shell', 'Run Chell'), ('stop process', 'Stop Process'),
    ('screen', 'Screenshot'), ('uninstall', 'Full Uninstall'), ('install', 'Install In OS'),
    ('update config', 'Update Config')])
    cmd = TextAreaField('Your command (cmd or path to file)')
    data = FileField('File')
    flag_wait_result = BooleanField('Wait Result')
    
    submit = SubmitField('Add New Task')