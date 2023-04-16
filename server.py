# flask
from flask import Flask, redirect, request, render_template, url_for, abort, jsonify, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# forms
from modules.forms import RegisterForm, LoginForm, NewsForm, DeleteForm, CommentForm, EditUserForm

# modules
from modules import db_session
from modules.user import User
from modules.news import News
from modules.comment import Comment

# other
import os
import datetime
import shutil

# api
from flask_restful import Api
from modules import users_resource
from modules import news_resource
from modules import comment_resource

from dotenv import load_dotenv

load_dotenv('.env.txt')

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'q1Nwjap1wbnhWghsYD7dRoNblMvEK6')

api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)


# routes
@app.route('/')
def main_page():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    first_images_urls = {}
    for i in news:
        first_images_urls[i.id] = url_for('static', filename=f'img/news/{i.id}/{i.images.split(";")[0]}')
    return render_template('main_page.html', title='main page',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/main_page.css'),
                           news=news, first_images_urls=first_images_urls)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='register',
                                   base_css=url_for('static', filename='css/base.css'),
                                   page_css=url_for('static', filename='css/form.css'),
                                   form=form, message='passwords do not match')

        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='register',
                                   base_css=url_for('static', filename='css/base.css'),
                                   page_css=url_for('static', filename='css/form.css'),
                                   form=form, message='user with that email already exists')

        filename = secure_filename(request.files['file_pfp'].filename)
        if filename != '' and filename.split(".")[-1] not in ('png', 'jpg', 'jpeg', 'bmp'):
            return render_template('register.html', title='register',
                                   base_css=url_for('static', filename='css/base.css'),
                                   page_css=url_for('static', filename='css/form.css'), form=form,
                                   message='Profile picture should be in png, jpg, jpeg or bmp format')

        user = User()
        user.nickname, user.email, user.about = form.nickname.data, form.email.data, form.about.data
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()

        filename = secure_filename(request.files['file_pfp'].filename)
        if filename != '':
            with open(f'static/img/users/{user.id}.{filename.split(".")[-1]}', mode='wb') as f:
                # if file is added we save it in news folder
                f.writelines(request.files['file_pfp'].readlines())
                user.image = f'{user.id}.{filename.split(".")[-1]}'
                db_sess.commit()

        return redirect('/login')
    return render_template('register.html', title='register',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'), form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        else:
            return render_template('login.html', title='login',
                                   base_css=url_for('static', filename='css/base.css'),
                                   page_css=url_for('static', filename='css/form.css'),
                                   message='wrong password or email', form=form)
    return render_template('login.html',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'), form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@login_required
@app.route('/news/add', methods=['GET', 'POST'])
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        for file in request.files.keys():
            filename = secure_filename(request.files[file].filename)
            if filename != '' and filename.split(".")[-1] not in ('png', 'jpg', 'jpeg', 'bmp'):
                return render_template('add_news.html', title='add news',
                                       base_css=url_for('static', filename='css/base.css'),
                                       page_css=url_for('static', filename='css/form.css'),
                                       form=form, message='All files should be in png, jpg, jpeg or bmp format')

        if form.tags.data != '' and form.tags.data[0] != '#':
            return render_template('add_news.html', title='add news',
                                   base_css=url_for('static', filename='css/base.css'),
                                   page_css=url_for('static', filename='css/form.css'),
                                   form=form, message='Incorrect tag: it should start with "#"')

        news = News(
            title=form.title.data,
            about=form.about.data
        )

        # tags
        news.tags = ';'.join(f' {form.tags.data}'.split(' #'))[1:] if len(form.tags.data) > 1 else ''
        # without repeat
        tags = set([i.strip() for i in news.tags.split(';')])
        print(news.tags)
        print(tags)
        news.tags = ';'.join(sorted(list(tags)))

        # we add the news so we can have the id and make files folder
        news.creator_id = current_user.id
        db_sess.add(news)
        db_sess.commit()

        # make a folder with name - id of added news
        if os.path.exists(f'static/img/news/{news.id}'):
            shutil.rmtree(f'static/img/news/{news.id}')
        os.makedirs(f'static/img/news/{news.id}')

        # images names
        images = []

        # we take all uploaded files and save them at news folder
        for file in request.files.keys():
            filename = secure_filename(request.files[file].filename)
            if filename != '':
                with open(f'static/img/news/{news.id}/{filename}', mode='wb') as f:
                    # if file is added we save it in news folder with picture number as name
                    f.writelines(request.files[file].readlines())
                images.append(filename)

        news.images = ';'.join(images)

        db_sess.commit()
        return redirect('/')
    return render_template('add_news.html', title='add news',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form)


@login_required
@app.route('/news/edit/<int:id>', methods=['GET', 'POST'])
def edit_news(id):
    form = NewsForm()

    if request.method == 'GET':
        # fill the form with already existing data
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.creator == current_user).first()
        if not news:
            abort(404)
        else:
            # fill the form
            form.title.data = news.title
            form.about.data = news.about
            form.tags.data = news.tags

    if form.validate_on_submit():
        # edit the news
        db_sess = db_session.create_session()
        news = db_sess.query(News).get(id)
        if not news:
            abort(404)

        # check if all uploaded files are images
        for file in request.files.keys():
            filename = secure_filename(request.files[file].filename)
            if filename != '' and filename.split(".")[-1] not in ('png', 'jpg', 'jpeg', 'bmp'):
                return render_template('edit_news.html', title='edit news',
                                       base_css=url_for('static', filename='css/base.css'),
                                       page_css=url_for('static', filename='css/form.css'),
                                       form=form, message='All files should be in png, jpg, jpeg or bmp format',
                                       imgs_urls=[url_for('static', filename=f'img/news/{news.id}/{i}')
                                                  for i in news.images.split(';')])

        news.title = form.title.data
        news.about = form.about.data
        news.tags = form.tags.data

        # edit files
        images = news.images.split(';')
        images = images + ['' for i in range(3 - len(images))]

        # if user wants to delete already existing file
        if form.file_1_ignore.data and images[0] != '':
            try:
                os.remove(f'static/img/news/{news.id}/{images[0]}')
            except FileNotFoundError:
                pass
            images[0] = ''
        if form.file_2_ignore.data and images[1] != '':
            try:
                os.remove(f'static/img/news/{news.id}/{images[1]}')
            except FileNotFoundError:
                pass
            images[1] = ''
        if form.file_3_ignore.data and images[2] != '':
            try:
                os.remove(f'static/img/news/{news.id}/{images[2]}')
            except FileNotFoundError:
                pass
            images[2] = ''

        for file in request.files.keys():
            filename = secure_filename(request.files[file].filename)

            if filename != '':
                with open(f'static/img/news/{news.id}/{filename}', mode='wb') as f:
                    # if file is added we save it in news folder
                    # and we delete old file

                    if form.file_1_ignore.data:
                        images[0] = ''
                        continue
                    if form.file_2_ignore.data:
                        images[1] = ''
                        continue
                    if form.file_3_ignore.data:
                        images[2] = ''
                        continue

                    f.writelines(request.files[file])
                    images[int(file[-1]) - 1] = filename

                news.images = ';'.join(list(filter(lambda x: x != '', images)))

        # if user wants to delete already existing file

        news.images = ';'.join(list(filter(lambda x: x != '', images)))

        db_sess.commit()
        return redirect('/')
    return render_template('edit_news.html', title='edit news',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form, imgs_urls=[url_for('static', filename=f'img/news/{news.id}/{i}')
                                                  for i in news.images.split(';')])


@login_required
@app.route('/news/delete/<int:id>', methods=['GET', 'POST'])
def delete_news(id):
    form = DeleteForm()

    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.creator == current_user).first()
    if not news:
        abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.creator == current_user).first()
        if not news:
            abort(404)

        shutil.rmtree(f'static/img/news/{news.id}')

        for com in news.comments:
            db_sess.delete(com)
        db_sess.commit()

        db_sess.delete(news)
        db_sess.commit()
        return redirect('/')
    return render_template('delete_news.html', title='delete news',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form, news=news,
                           img_url=url_for('static',
                                           filename=f'img/news/{news.id}/{news.images.split(";")[0]}'
                                           if news.images else ''))


@login_required
@app.route('/news/<int:id>', methods=['GET', 'POST'])
def news_show(id):
    form = CommentForm()
    db_sess = db_session.create_session()
    news = db_sess.query(News).get(id)
    if not news:
        abort(404)

    # data about commentators
    comments_creators_dict = {}
    for i in news.comments:
        user = db_sess.query(User).filter(User.id == i.creator_id).first()
        if user:
            comments_creators_dict[i.id] = user

    # comments users images
    comments_creators_imgs_urls = {}
    for i in news.comments:
        comments_creators_imgs_urls[i.id] = \
            url_for('static', filename=f'img/users/{comments_creators_dict[i.id].image}')

    # news images
    news_images_url = [url_for('static', filename=f'img/news/{id}/{i}') for i in news.images.split(';')]

    if form.validate_on_submit():
        comment = Comment(
            text=form.text.data,
            creator_id=current_user.id,
            news_id=id
        )
        db_sess = db_session.create_session()
        db_sess.add(comment)
        db_sess.commit()
        return redirect(f'/news/{id}')
    return render_template('one_news_show.html', title='news',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/one_news_page.css'),
                           form=form, comments_creators_dict=comments_creators_dict, news=news,
                           news_images_url=news_images_url,
                           creator_img_url=url_for('static', filename=f'img/users/{news.creator.image}'),
                           comments_creators_imgs_urls=comments_creators_imgs_urls,
                           comments=sorted(news.comments, key=lambda x: x.creation_date, reverse=True))


@app.route('/user/profile/<int:id>', methods=['GET', 'POST'])
def show_user(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(id)
    if not user:
        abort(404)

    first_images_urls = {}
    for i in user.news:
        first_images_urls[i.id] = url_for('static', filename=f'img/news/{i.id}/{i.images.split(";")[0]}')

    return render_template('profile.html', title='profile',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/profile_page.css'),
                           user_img_url=url_for('static', filename=f'img/users/{user.image}'),
                           user=user, first_images_urls=first_images_urls,
                           user_news=sorted(user.news, key=lambda x: x.creation_date, reverse=True))


@login_required
@app.route('/user/profile/delete/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    form = DeleteForm()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id, User.id == current_user.id).first()
    if not user:
        abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id, User.id == current_user.id).first()
        if not user:
            abort(404)

        for news in user.news:
            news.creator_id = 1
        db_sess.commit()

        user_comments = db_sess.query(Comment).filter(Comment.creator_id == user.id)
        for comment in user_comments:
            db_sess.delete(comment)

        db_sess.delete(user)
        db_sess.commit()
        logout_user()
        return redirect('/')
    return render_template('delete_user.html', title='delete user',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form, user=user, user_pfp_url=url_for('static', filename=f'img/users/{user.image}'))


@login_required
@app.route('/user/profile/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    form = EditUserForm()

    if request.method == 'GET':
        # fill the form with already existing data
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id, User.id == current_user.id).first()
        if not user:
            abort(404)
        else:
            form.email.data = user.email
            form.about.data = user.about
            form.nickname.data = user.nickname

    if form.validate_on_submit():
        # edit the user
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id, User.id == current_user.id).first()
        if not user:
            abort(404)

        if not form.password.data == form.password_again.data:
            return render_template('edit_user.html', title='edit user',
                                   base_css=url_for('static', filename='css/base.css'),
                                   page_css=url_for('static', filename='css/form.css'),
                                   form=form, message='Passwords should match')

        # if prfile picture (pfp) is in wrong format we tell user about it
        filename = secure_filename(request.files['file_pfp'].filename)
        if filename != '' and filename.split(".")[-1] not in ('png', 'jpg', 'jpeg', 'bmp'):
            return render_template('edit_user.html', title='edit user',
                                   base_css=url_for('static', filename='css/base.css'),
                                   page_css=url_for('static', filename='css/form.css'),
                                   form=form, message='Profile picture should be in png, jpg, jpeg or bmp format')

        user.nickname = form.nickname.data
        user.about = form.about.data
        user.email = form.email.data

        if form.password.data != '':
            user.set_password(form.password.data)

        # if file is here we update pfp
        if filename != '':
            try:
                os.remove(f'static/img/users/{user.image}')
            except FileNotFoundError:
                pass
            with open(f'static/img/users/{user.id}.{filename.split(".")[-1]}', mode='wb') as f:
                # if file is added we save it in news folder
                # and we delete old file
                f.writelines(request.files['file_pfp'].readlines())
                user.image = f'{user.id}.{filename.split(".")[-1]}'

        # if user wants to delete pfp and box is checked we delete the file
        if form.ignore_pfp.data:
            try:
                os.remove(f'static/img/users/{user.image}')
            except FileNotFoundError:
                pass
            user.image = 'no_pfp.png'

        db_sess.commit()
        return redirect(f'/user/profile/{user.id}')
    return render_template('edit_user.html', title='edit user',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form)


@login_required
@app.route('/comments/delete/<int:id>', methods=['GET', 'POST'])
def delete_comment(id):
    form = DeleteForm()
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == id, Comment.creator_id == current_user.id).first()
    if not comment:
        abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        comment = db_sess.query(Comment).filter(Comment.id == id, Comment.creator_id == current_user.id).first()
        if not comment:
            abort(404)

        news_id = comment.news.id

        db_sess.delete(comment)
        db_sess.commit()
        return redirect(f'/news/{news_id}')
    return render_template('delete_comment.html', title='delete comment',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form, comment=comment,)


@login_required
@app.route('/comments/edit/<int:id>', methods=['GET', 'POST'])
def edit_comment(id):
    form = CommentForm()
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == id, Comment.creator_id == current_user.id).first()
    if not comment:
        abort(404)

    if request.method == 'GET':
        form.text.data = comment.text

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        comment = db_sess.query(Comment).filter(Comment.id == id, Comment.creator_id == current_user.id).first()
        if not comment:
            abort(404)

        comment.text = form.text.data
        comment.creation_date = datetime.datetime.now()
        comment.is_edited = True

        db_sess.commit()
        return redirect(f'/news/{comment.news.id}')
    return render_template('edit_comment.html', title='edit comment',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form, comment=comment)


@app.route('/news/search', methods=['GET', 'POST'])
def search_tagged_news_form():
    form = CommentForm()

    if form.validate_on_submit():
        return redirect(f'/news/search/{";".join((form.text.data[1:]).rstrip().split(" #"))}')
    return render_template('news_search.html', title='news search',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/form.css'),
                           form=form)


@app.route('/news/search/<tags>', methods=['GET', 'POST'])
def search_tagged_news(tags):
    db_sess = db_session.create_session()

    # find tagged news
    news = list(filter(lambda x: all([tag in x.tags.split(';') for tag in tags.split(';')]), db_sess.query(News).all()))

    # same with main page
    first_images_urls = {}
    for i in news:
        first_images_urls[i.id] = url_for('static', filename=f'img/news/{i.id}/{i.images.split(";")[0]}')

    return render_template('main_page.html', title='main page',
                           base_css=url_for('static', filename='css/base.css'),
                           page_css=url_for('static', filename='css/main_page.css'),
                           news=news, first_images_urls=first_images_urls)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


def main():
    db_session.global_init('db/data.db')

    db_sess_first = db_session.create_session()
    if db_sess_first.query(User).get(1) is None:
        user = User(
            nickname='deleted user',
            image='dead_user.png'
        )
        db_sess_first.add(user)
        db_sess_first.commit()
    
    # api
    api.add_resource(users_resource.UserResource, '/api/users/<int:user_id>')
    api.add_resource(users_resource.UserListResource, '/api/users')

    api.add_resource(news_resource.NewsResource, '/api/news/<int:news_id>')
    api.add_resource(news_resource.NewsListResource, '/api/news')

    api.add_resource(comment_resource.CommentResource, '/api/comments/<int:com_id>')
    api.add_resource(comment_resource.CommentListResource, '/api/comments')

    app.run(port=5000, host='127.0.0.1')


if __name__ == '__main__':
    main()
