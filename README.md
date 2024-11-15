# IIT Polling Platform

This is a multi-tenant polling platform designed for use by multiple institutions, allowing students to participate in polls and administrators to manage and view poll results. The platform is built with Flask and follows a Pub/Sub architecture for real-time updates. It supports deployment on Google Cloud using Docker and Cloud Run. Our application is live on https://iitjpoll-7suqwt5voq-el.a.run.app 

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Pub/Sub System](#pubsub-system)
- [Deployment](#deployment)
- [Technologies Used](#technologies-used)
- [Contributors](#contributors)

---

## Features

- **Multi-tenant Structure**: Supports multiple institutions with separate data management.
- **Role-based Access**: Admin and Student roles with distinct interfaces and permissions.
- **Poll Management**: Admins can create, edit, and delete polls, and view poll results.
- **Voting System**: Students can participate in polls and view results.
- **Real-time Updates**: Uses a Pub/Sub model to ensure all users see the latest poll data.
- **Cloud Deployment**: Ready for deployment on Google Cloud using Docker and Cloud Run.

---

## Project Structure

```plaintext
IITJ-Polling-Platform/
├── Dataset/              # Initial data files for loading into the platform
├── instance/             # Instance-specific configurations (e.g., secrets)
├── migrations/           # Database migration files
├── Template/             # HTML templates for the web interface
├── __pycache__/          # Cached files
├── app.py                # Main application file
├── config.py             # Configuration settings (database URIs, environment variables)
├── data_loader.py        # Script to load data into the platform
├── dockerfile            # Dockerfile for building the container
├── init_db.py            # Script to initialize database schema
├── models.py             # Defines database models (User, Poll, Vote)
├── polling_platform.db   # SQLite database (for local testing)
├── pubsub.py             # Pub/Sub system for real-time notifications
├── README.md             # Project documentation
└── requirements.txt      # List of dependencies
```

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- Docker
- Google Cloud SDK (for deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/IITJ-Polling-Platform.git
   cd IITJ-Polling-Platform
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**:
   - Run the following commands to initialize the database:
     ```bash
     python init_db.py
     python data_loader.py
     ```

4. **Environment Configuration**:
   - Update the `config.py` file with your database URIs and other configurations as needed.

5. **Run the Application**:
   ```bash
   python app.py
   ```

The application should be accessible at `http://localhost:5000`.

---

## Usage

1. **Admin Login**:
   - Access the Admin Dashboard to create, edit, or delete polls.
   - View poll results and publish polls.

2. **Student Login**:
   - View and participate in active polls.
   - See results of previous polls once they are published.

### Note
Admins and students have different permissions and views. Ensure to select the correct role when logging in.

---

## Pub/Sub System

The `pubsub.py` file implements a basic Publish/Subscribe system. This system:
- Notifies subscribers (e.g., students and admins) of new or updated polls.
- Provides real-time updates to ensure users see the most current poll data.
- Allows efficient communication between different components in a scalable manner.

---

## Deployment

To deploy on Google Cloud using Docker and Cloud Run:

1. **Build the Docker image**:
   ```bash
   docker build -t iit-polling-platform .
   ```

2. **Push to Google Container Registry**:
   ```bash
   docker tag iit-polling-platform gcr.io/[YOUR_PROJECT_ID]/iit-polling-platform
   docker push gcr.io/[YOUR_PROJECT_ID]/iit-polling-platform
   ```

3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy iit-polling-platform --image gcr.io/[YOUR_PROJECT_ID]/iit-polling-platform --platform managed
   ```

Make sure to replace `[YOUR_PROJECT_ID]` with your Google Cloud project ID.

---

## Technologies Used

- **Backend**: Python, Flask
- **Database**: SQLite (for local testing), compatible with Cloud SQL for production
- **Containerization**: Docker
- **Real-Time Updates**: Pub/Sub system
- **Cloud Platform**: Google Cloud (Cloud Run)

---

## Contributors

- **Name** - [Atriz Ray](https://github.com/AtrizRay) , [Nidhi Rani](https://github.com/NIDHIRANI-PROG) , [Subham Roy]
- **Project Mentor** - Sumit Kalra

---
