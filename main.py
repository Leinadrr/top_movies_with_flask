from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import InputRequired
import requests
import os


# Configuracion de flask, base de datos, bootstrap y constantes #
app = Flask(__name__)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top_movies.db"
db.init_app(app)
bootstrap = Bootstrap5(app)
app.secret_key = os.environ.get("FLASK-SECRET-KEY")
MOVIE_API = "0025706f77c4eede0c4cb28f1adda74e"
MOVIE_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_ID_URL = "https://api.themoviedb.org/3/movie/"
IMAGE_PATH = "https://image.tmdb.org/t/p/original/"


# Definición de formularios para flask-wtf #
class MyForm(FlaskForm):
    rating = FloatField("Your rating out of 10, e.g. 7.5", [InputRequired()])
    review = StringField("Your review", [InputRequired()])
    submit = SubmitField("Done")


class AddForm(FlaskForm):
    movie_title = StringField("Movie Title", [InputRequired()])
    submit = SubmitField("Add movie")


# Definición y creación del modelo de tabla para flask-sqlalchemy #
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(350), nullable=True)
    img_url = db.Column(db.String, nullable=True)
# with app.app_context():                  // uncomment this lines to create de data base.
#     db.create_all()


# Ejemplo de consulta de introducción de datos manual en db #
# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an
#         extortionist's "
#                     "sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the
#                     caller leads "
#                     "to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()


# Ruta / y función de tarjetas ordenadas por ranking #
@app.route("/")
def home():
    movie_data = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for i in enumerate(movie_data.__reversed__(), 1):
        movie_rank = i[0]
        i[1].ranking = movie_rank
    db.session.commit()
    return render_template("index.html", data=movie_data)


# Edición del rating y opinión de las películas #
@app.route("/edit", methods=["GET", "POST"])
def update_rating():
    form = MyForm()
    movie_id = request.args.get("id")
    movie = db.session.execute(db.select(Movie).filter_by(id=movie_id)).scalar()
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie, form=form)


# Función para borrar las películas de la db #
@app.route("/del")
def delete_movie():
    with app.app_context():
        movie_id = request.args.get("id")
        movie = db.session.execute(db.select(Movie).filter_by(id=movie_id)).scalar()
        db.session.delete(movie)
        db.session.commit()
    return redirect(url_for("home"))


# Función para añadir nuevas películas a la app y recuperar información de una api #
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddForm()
    movie = form.movie_title.data
    if form.validate_on_submit():
        response = requests.get(MOVIE_SEARCH_URL, params={"api_key": MOVIE_API, "query": movie})
        response.raise_for_status()
        movie_search = response.json()
        return render_template("select.html", movies=movie_search["results"])
    return render_template("add.html", form=form)


# Función que añade la información de la api a entrada de la peli en la db #
@app.route("/todb")
def add_movie_to_db():
    movie_id = request.args.get("id")
    response = requests.get(MOVIE_ID_URL+movie_id, params={"api_key": MOVIE_API})
    movie_data = response.json()
    title = movie_data["original_title"]
    year = movie_data["release_date"]
    overview = movie_data["overview"]
    img = movie_data["poster_path"]

    new_movie = Movie(
            title=title,
            year=year,
            description=overview,
            img_url=IMAGE_PATH+img
        )

    db.session.add(new_movie)
    db.session.commit()
    id1 = db.session.execute(db.select(Movie).filter_by(title=title)).scalar()
    bd_movie_id = id1.id
    return redirect(url_for("update_rating", id=bd_movie_id))


if __name__ == '__main__':
    app.run(debug=True)
