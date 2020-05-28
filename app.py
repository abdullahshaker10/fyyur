#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import ast

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.sql import func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(110))
    image_link = db.Column(db.String(500))

    genres = db.relationship('Genre', backref=db.backref("venue"))

    atists = db.relationship(
        'Artist',
        secondary='show'
    )


    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(120))

    genres = db.relationship('Genre', backref=db.backref("artist"))

    venues = db.relationship(
        'Venue',
        secondary='show'
    )


class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id))
    venue_id = db.Column(db.Integer,  db.ForeignKey(Venue.id))
    start_time = db.Column(db.DateTime, default = db.func.now())
    artist = db.relationship(Artist, backref=db.backref("artist_assoc"))
    venue = db.relationship(Venue, backref=db.backref("venue_assoc"))

class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name =  db.Column(db.String(120))
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id))
    venue_id = db.Column(db.Integer,  db.ForeignKey(Venue.id))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # grouped_venues =  db.session.query(Venue.name, func.count(Venue.city)).group_by(Venue.city).all()

  data = []
  venue_groups = db.session.query(Venue.city, Venue.state, func.count(Venue.city), 
  func.count(Venue.state)).group_by(Venue.city, Venue.state).all()

  for i in range(len(venue_groups)):
    data_dict = {}
    
    filterd_venues = Venue.query.filter_by(city=venue_groups[i][0], state=venue_groups[i][1]).all()

    data_dict['city'] = filterd_venues[0].city
    data_dict['state'] = filterd_venues[0].state

    venue_list = []
    for venue in filterd_venues:
        venue_dict = {}
        venue_dict['id'] = venue.id
        venue_dict['name'] = venue.name  

        venue_dict['num_upcoming_shows'] = Show.query.filter_by(venue_id = venue.id ).filter(Show.start_time > datetime.now()).count()

        venue_list.append(venue_dict)
    data_dict['venues']= venue_list

    data.append(data_dict)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
 
  search_term = request.form.get('search_term')
  search = "%{}%".format(search_term)
  venues = Venue.query.filter(func.lower(Venue.name).like(func.lower(search))).all()

  response = {}
  data = []
  for venue in venues:
    dict = {}
    dict['id'] = venue.id
    dict['name'] = venue.name
    data.append(dict)
  response['count'] = len(data)
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term'))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.get(venue_id)
  data = venue.__dict__
  genre_list = []

  for genre in venue.genres:
    genre_list.append(genre.name)
  data['genres'] = genre_list

  comming_shows = []
  past_shows = []

  shows = Show.query.filter_by(venue_id = venue_id).filter(Show.start_time < datetime.now()).all() 
  for show in shows:
    dict = {}
    dict['artist_id'] = show.artist_id
    artist = Artist.query.get(show.artist_id)

    dict['artist_name'] = artist.name
    dict['artist_image_link'] = artist.image_link
    dict['start_time'] = str(show.start_time)

    past_shows.append(dict)

  data['past_shows'] = past_shows

  shows = Show.query.filter_by(venue_id = venue_id).filter(Show.start_time > datetime.now()) 
  for show in shows:
    dict = {}
    dict['artist_id'] = show.artist_id
    artist = Artist.query.get(show.artist_id)

    dict['artist_name'] = artist.name
    dict['artist_image_link'] = artist.image_link
    dict['start_time'] = str(show.start_time)

    comming_shows.append(dict)
    
  data['upcoming_shows'] = comming_shows

  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(comming_shows)
  #data.pop('_sa_instance_state')

  #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    facebook_link = request.form.get('facebook_link')
    genres = request.form.getlist('genres')
    image_link = request.form.get('image_link')
    seeking_talent = bool(request.form.get('seeking_talent'))
    website_link = request.form.get('website_link')
    seeking_description = request.form.get('seeking_description')

    venue = Venue(name = name, city = city, state = state, 
                  address = address, phone = phone, facebook_link = facebook_link,
                  image_link = image_link,seeking_talent=seeking_talent,
                   website_link = website_link, seeking_description = seeking_description)

    for name in genres:
        g= Genre(name = name)
        venue.genres.append(g)
      
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success

    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
  finally:
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = Artist.query.all()
  for artist in artists:
    artist_dict = {}
    artist_dict['id'] = artist.id
    artist_dict['name'] = artist.name
    data.append(artist_dict)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
 
  search_term = request.form.get('search_term')
  search = "%{}%".format(search_term)
  artists = Artist.query.filter(func.lower(Artist.name).like(func.lower(search))).all()

  response = {}
  data = []
  for artist in artists:
    dict = {}
    dict['id'] = artist.id
    dict['name'] = artist.name
    data.append(dict)
    
  response['count'] = len(data)
  response['data'] = data
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term'))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
 
  artist = Artist.query.get(artist_id)
  data = artist.__dict__
  genre_list = []

  for genre in artist.genres:
    genre_list.append(genre.name)

  data['genres'] = genre_list
  comming_shows = []
  past_shows = []
  shows = Show.query.filter_by(artist_id = artist_id).filter(Show.start_time < datetime.now()).all() 
  for show in shows:
    dict = {}
    dict['venue'] = show.venue_id
    venue = Venue.query.get(show.venue_id)
    dict['venue_name'] = venue.name
    dict['venue_image_link'] = venue.image_link
    dict['start_time'] = str(show.start_time)
    past_shows.append(dict)

  data['past_shows'] = past_shows
  shows = Show.query.filter_by(artist_id = artist_id).filter(Show.start_time > datetime.now()) 
  for show in shows:
    dict = {}
    dict['venue_id'] = show.venue_id
    venue = Venue.query.get(show.venue_id)
    dict['venue_name'] = venue.name
    dict['venue_image_link'] = venue.image_link
    dict['start_time'] = str(show.start_time)
    comming_shows.append(dict)
    
  data['upcoming_shows'] = comming_shows 
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(comming_shows)
  #data.pop('_sa_instance_state')
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  genres = [genre.name for genre in artist.genres]
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist,genres=genres)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.filter_by(id=artist_id).one()

  name = request.form.get('name')
  city = request.form.get('city')
  state = request.form.get('state')
  address = request.form.get('address')
  phone = request.form.get('phone')
  facebook_link = request.form.get('facebook_link')
  genres = request.form.getlist('genres')
  image_link = request.form.get('image_link')
  seeking_talent = bool(request.form.get('seeking_talent'))
  website_link = request.form.get('website_link')
  seeking_description = request.form.get('seeking_description')


  artist.name = name 
  artist.city = city 
  artist.state = state 
  artist.address = address 
  artist.facebook_link = facebook_link 
  artist.phone = phone 
  artist.image_link = image_link 
  artist.website_link = website_link 
  artist.seeking_talent = seeking_talent 
  artist.seeking_description = seeking_description 

  artist.genres = []

  for name in genres:
        g= Genre(name = name)
        artist.genres.append(g)

  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  genres = [genre.name for genre in venue.genres ]
  return render_template('forms/edit_venue.html', form=form, venue=venue, genres=genres)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.filter_by(id=venue_id).one()

  name = request.form.get('name')
  city = request.form.get('city')
  state = request.form.get('state')
  address = request.form.get('address')
  phone = request.form.get('phone')
  facebook_link = request.form.get('facebook_link')
  genres = request.form.getlist('genres')
  image_link = request.form.get('image_link')
  seeking_talent = bool(request.form.get('seeking_talent'))
  website_link = request.form.get('website_link')
  seeking_description = request.form.get('seeking_description')


  venue.name = name 
  venue.city = city 
  venue.state = state 
  venue.address = address 
  venue.facebook_link = facebook_link 
  venue.phone = phone 
  venue.image_link = image_link 
  venue.website_link = website_link 
  venue.seeking_talent = seeking_talent 
  venue.seeking_description = seeking_description 

  venue.genres = []

  for name in genres:
        g= Genre(name = name)
        venue.genres.append(g)

  db.session.commit()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  try:
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    seeking_talent = bool(request.form.get('seeking_talent'))
    website_link = request.form.get('website_link')
    seeking_description = request.form.get('seeking_description')
    image_link = request.form.get('image_link')

    artist = Artist(name=name, city=city, state=state, phone=phone, 
          facebook_link=facebook_link, seeking_talent=seeking_talent,
          website_link = website_link,seeking_description = seeking_description,
          image_link = image_link)

    for name in genres:
        g= Genre(name = name)
        artist.genres.append(g)

    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!') 

  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')

  finally:
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  data = []

  shows =Show.query.all()

  for show in shows:
    show_dict = {}
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    
    show_dict['venue_id'] = show.venue_id
    show_dict['venue_name'] = venue.name
    show_dict['artist_id'] = show.artist_id
    show_dict['artist_name'] = artist.name
    show_dict['artist_image_link'] = artist.image_link
    show_dict['start_time'] = str(show.start_time)
    data.append(show_dict)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')
    
    show = Show(artist_id = artist_id, venue_id = venue_id, start_time = start_time )

    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')

  finally:
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
