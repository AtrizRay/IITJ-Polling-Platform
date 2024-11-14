import os
import json
import webbrowser
import argparse
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from models import db, User, Poll, Vote
from collections.abc import MutableMapping
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'choose_login'

def init_db():
    """Initialize the database by creating all tables."""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

def load_data_from_csv():
    """Load data from CSV files."""
    csv_path = os.path.join(os.path.dirname(__file__), 'Database')
    try:
        global_admin = pd.read_csv(os.path.join(csv_path, 'global_admin.csv'))
        local_admin_1 = pd.read_csv(os.path.join(csv_path, 'local_admin_institute_1.csv'))
        local_admin_2 = pd.read_csv(os.path.join(csv_path, 'local_admin_institute_2.csv'))
        student_data_1 = pd.read_csv(os.path.join(csv_path, 'student_data_institute_1.csv'))
        student_data_2 = pd.read_csv(os.path.join(csv_path, 'student_data_institute_2.csv'))
        polls_1 = pd.read_csv(os.path.join(csv_path, 'polls_institute_1.csv'))
        polls_2 = pd.read_csv(os.path.join(csv_path, 'polls_institute_2.csv'))
        logger.info("CSV files loaded successfully.")
        return global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2, polls_1, polls_2
    except Exception as e:
        logger.error(f"Error loading CSV files: {str(e)}")
        return None

def add_users_from_dataframe(df):
    """Add users from a DataFrame to the database."""
    try:
        for index, row in df.iterrows():
            logger.debug(f"Processing user: {row.to_dict()}")
            existing_user = User.query.filter_by(username=row['username']).first()
            
            if existing_user:
                existing_user.password = generate_password_hash(str(row['password']), method='pbkdf2:sha256')
                existing_user.user_type = row['user_type']
                existing_user.institute_id = str(row.get('institute_id', ''))
                logger.debug(f"User {row['username']} updated.")
            else:
                user = User(
                    username=row['username'],
                    name=row.get('name', row['username']),
                    password=generate_password_hash(str(row['password']), method='pbkdf2:sha256'),
                    user_type=row['user_type'],
                    institute_id=str(row.get('institute_id', ''))
                )
                db.session.add(user)
                logger.debug(f"User {row['username']} added.")
        
        db.session.commit()
    except Exception as e:
        logger.error(f"Error adding users from DataFrame: {str(e)}")
        db.session.rollback()
        raise

def add_polls_from_dataframe(polls_df):
    """Add polls from a DataFrame to the database."""
    try:
        for _, row in polls_df.iterrows():
            try:
                # Get the options string and split it into a list
                options_str = str(row['options']).strip()
                options_list = [opt.strip() for opt in options_str.split(',') if opt.strip()]
                
                # Check if poll already exists
                existing_poll = Poll.query.filter_by(
                    question=row['question'],
                    institute_id=str(row['institute_id'])
                ).first()
                
                if not existing_poll:
                    # Create new poll with proper initialization
                    new_poll = Poll(
                        question=row['question'],
                        institute_id=str(row['institute_id']),
                        institute=row.get('institute', f'Institute {row["institute_id"]}'),
                        responses={}
                    )
                    # Set options using the helper method
                    new_poll.set_options(options_list)
                    
                    db.session.add(new_poll)
                    logger.debug(f"Adding new poll: {row['question']} with options: {options_list}")
                
            except Exception as row_error:
                logger.error(f"Error processing row: {row}")
                logger.error(f"Row error details: {str(row_error)}")
                continue
        
        db.session.commit()
        logger.info("Successfully added all valid polls to database")
        
    except Exception as e:
        logger.error(f"Error adding polls from DataFrame: {str(e)}")
        logger.error(f"Full error details: {str(e.__class__.__name__)}: {str(e)}")
        db.session.rollback()
        raise

def validate_polls_data(polls_df):
    """Validate polls data before processing"""
    required_columns = ['question', 'options', 'institute_id', 'institute']
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in polls_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Clean and validate data
    cleaned_df = polls_df.copy()
    
    # Ensure options are strings
    cleaned_df['options'] = cleaned_df['options'].astype(str)
    
    # Ensure institute_id is string
    cleaned_df['institute_id'] = cleaned_df['institute_id'].astype(str)
    
    # Remove any rows with empty questions or options
    cleaned_df = cleaned_df.dropna(subset=['question', 'options'])
    
    return cleaned_df

def initialize_data():
    """Initialize data in the database from CSV files."""
    try:
        # First, ensure database tables exist
        init_db()
        
        # Load CSV data
        data = load_data_from_csv()
        if data is None:
            logger.error("Failed to load CSV data.")
            return

        global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2, polls_1, polls_2 = data

        # Add users
        for df in [global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2]:
            add_users_from_dataframe(df)
        
        # Validate and add polls
        for polls_df in [polls_1, polls_2]:
            validated_df = validate_polls_data(polls_df)
            add_polls_from_dataframe(validated_df)

        logger.info("Data initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error during data initialization: {str(e)}")
        raise

@login_manager.user_loader
def load_user(user_id):
    """Load a user by ID."""
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    """Home page route."""
    return redirect(url_for('choose_login'))

@app.route('/choose_login', methods=['GET'])
def choose_login():
    """Route for selecting login type."""
    return render_template('login.html')

def login_user_by_type(user_type, redirect_view):
    """Generic user login logic."""
    try:
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.user_type == user_type and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for(redirect_view))
        else:
            flash('Invalid credentials')
        return render_template('login.html', login_type=user_type)
    except Exception as e:
        logger.error(f"Error in login process: {str(e)}")
        flash('An error occurred during login')
        return render_template('login.html', login_type=user_type)

@app.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login route."""
    if request.method == 'POST':
        return login_user_by_type('master_admin', 'master_admin_dashboard')
    return render_template('login.html', login_type='admin')

@app.route('/login/local_admin', methods=['GET', 'POST'])
def local_admin_login():
    """Local admin login route."""
    if request.method == 'POST':
        return login_user_by_type('local_admin', 'local_admin_dashboard')
    return render_template('login.html', login_type='local_admin')

@app.route('/login/student', methods=['GET', 'POST'])
def student_login():
    """Student login route."""
    if request.method == 'POST':
        return login_user_by_type('student', 'landing')
    return render_template('login.html', login_type='student')

@app.route('/logout')
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    return redirect(url_for('choose_login'))

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard route."""
    if current_user.user_type == 'master_admin':
        return redirect(url_for('master_admin_dashboard'))
    elif current_user.user_type == 'local_admin':
        return redirect(url_for('local_admin_dashboard'))
    else:
        return redirect(url_for('landing'))

@app.route('/master_admin_dashboard')
@login_required
def master_admin_dashboard():
    """Master admin dashboard route."""
    if current_user.user_type != 'master_admin':
        return redirect(url_for('landing'))
    try:
        polls = Poll.query.all()
        users = User.query.all()
        options = {poll.id: poll.responses for poll in polls}
        return render_template('admin.html', admin_type='master', polls=polls, users=users, options=options)
    except Exception as e:
        logger.error(f"Error in master admin dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard')
        return redirect(url_for('home'))

@app.route('/local_admin_dashboard')
@login_required
def local_admin_dashboard():
    """Local admin dashboard route."""
    if current_user.user_type != 'local_admin':
        return redirect(url_for('landing'))
    try:
        polls = Poll.query.filter_by(institute_id=current_user.institute_id).all()
        options = {poll.id: poll.responses for poll in polls}
        return render_template('admin.html', admin_type='local', polls=polls, options=options)
    except Exception as e:
        logger.error(f"Error in local admin dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard')
        return redirect(url_for('home'))

@app.route('/landing')
@login_required
def landing():
    """Landing page for students."""
    try:
        institute_id = current_user.institute_id
        all_polls = Poll.query.filter_by(institute_id=institute_id).all()
        
        unvoted_polls = []
        voted_polls = []
        options = {}

        for poll in all_polls:
            poll_data = {
                'id': poll.id,
                'question': poll.question,
                'responses': poll.responses
            }
            poll_options = poll.get_options()
            options[poll.id] = poll_options

            # Check if the current user has voted on this poll
            if str(current_user.id) in poll.responses:
                voted_polls.append(poll_data)
                logger.debug(f"Poll {poll.id} added to voted_polls.")
            else:
                unvoted_polls.append(poll_data)
                logger.debug(f"Poll {poll.id} added to unvoted_polls.")

        return render_template('landing.html', 
                               unvoted_polls=unvoted_polls, 
                               voted_polls=voted_polls, 
                               options=options)
    except Exception as e:
        logger.error(f"Error in landing page: {str(e)}")
        flash('An error occurred while loading the polls')
        return redirect(url_for('home'))


@app.route('/vote/<int:poll_id>', methods=['POST'])
@login_required
def vote(poll_id):
    """Vote on a poll."""
    try:
        poll = Poll.query.get(poll_id)
        
        if not poll:
            flash('Poll not found')
            return redirect(url_for('landing'))

        # Retrieve the selected option by constructing the expected form name
        option = request.form.get(f'option_{poll_id}')
        
        if not option:
            flash('No option selected')
            return redirect(url_for('landing'))

        # Check if the user has already voted
        if str(current_user.id) in poll.responses:
            flash('You have already voted on this poll')
            return redirect(url_for('landing'))

        # Record the vote and save to database
        poll.responses[str(current_user.id)] = option
        
        # Explicitly tell SQLAlchemy to mark the field as modified
        db.session.add(poll)  # Add poll back to session to ensure it updates
        db.session.commit()  # Make sure vote is saved
        
        # Debug log to confirm vote saving
        logger.debug(f"Vote recorded for poll {poll.id}: {poll.responses}")
        
        flash('Thank you for voting!')
        return redirect(url_for('landing'))
    except Exception as e:
        logger.error(f"Error processing vote: {str(e)}")
        flash('An error occurred while processing your vote')
        return redirect(url_for('landing'))



@app.route('/results', methods=['GET'])
@login_required
def results():
    """Display poll results for all polls."""
    try:
        # Get all polls for the current user's institute
        #polls = Poll.query.filter_by(institute_id=current_user.institute_id).all()
        polls = Poll.query.all()
        
        if not polls:
            flash('No polls found for your institute.')
            return redirect(url_for('landing'))

        # Process each poll's responses
        poll_results = []
        for poll in polls:
            # Get the options for this poll
            options = poll.get_options()
            
            # Initialize vote counts for each option
            vote_counts = {option: 0 for option in options}
            
            # Count votes for each option
            if poll.responses:
                for vote in poll.responses.values():
                    if vote in vote_counts:
                        vote_counts[vote] += 1
            
            # Calculate total votes
            total_votes = sum(vote_counts.values())
            
            # Calculate percentages
            vote_percentages = {}
            for option, count in vote_counts.items():
                percentage = (count / total_votes * 100) if total_votes > 0 else 0
                vote_percentages[option] = round(percentage, 1)
            
            poll_data = {
                'id': poll.id,
                'question': poll.question,
                'total_votes': total_votes,
                'vote_counts': vote_counts,
                'vote_percentages': vote_percentages
            }
            poll_results.append(poll_data)
        
        # Render the template with cache-busting headers
        response = make_response(render_template(
            'results.html',
            polls=poll_results
        ))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        return response

    except Exception as e:
        logger.error(f"Error displaying results: {str(e)}")
        flash('An error occurred while fetching poll results.')
        return redirect(url_for('landing'))



if __name__ == '__main__':
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run the Flask application.')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the Flask app on.')
    parser.add_argument('--tenant', type=str, default='default', help='Tenant identifier.')
    args = parser.parse_args()

    # Initialize the database and load data
    with app.app_context():
        try:
            initialize_data()
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            exit(1)
    
    # Automatically open the app in Chrome
    try:
        webbrowser.open_new(f'http://127.0.0.1:{args.port}')
    except Exception as e:
        logger.error(f"Failed to open browser: {str(e)}")
    
    # Run the app
    app.run(port=args.port, debug=True)