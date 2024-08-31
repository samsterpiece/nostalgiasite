# 🕹️ Nostalgia Site 🕹️

Welcome to the Nostalgia Site, a blast from the past where you can relive the glory days of the early internet! 🌐🚀

## 🎮 Getting Started 🎮

To get started with the Nostalgia Site, follow these steps to set up your local environment. Let's take a trip back in time! 🕰️

### 🛠️ Setting Up Postgres 🛠️


1. **Install Postgres**:
   - **Mac**: Use Homebrew with `brew install postgresql`.
   - **Windows**: Download and install from [Postgres.app](https://postgres.app).
   - **Linux**: Use your package manager, e.g., `sudo apt-get install postgresql postgresql-contrib`.


2. **Start Postgres**:
   - **Mac/Linux**: Run `pg_ctl -D /usr/local/var/postgres -l /usr/local/var/postgres/server.log start`.
   - **Windows**: Start the Postgres service from the Services application or command line.


3. **Create a Database**:
   - Open a terminal and connect to Postgres: `psql -U postgres`.
   - Create a new database: `CREATE DATABASE nostalgia_db;`.

### 📦 Installing Requirements 📦


1. **Clone the Repository**:
   ```sh
   git clone https://github.com/yourusername/nostalgia-site.git
   cd nostalgia-site

2. **Install Python Requirements**:
   ```sh
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   - Ensure you have the necessary environment variables set up in your `.env` file:
     ```
     DATABASE_URL=postgres://username:password@localhost:5432/nostalgia_db
     SECRET_KEY=your_secret_key
     DEBUG=True
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

### 🚀 Running the Application 🚀

1. **Migrate the Database**:
   ```sh
   python manage.py migrate
   ```

2. **Create a Superuser (Optional)**:
   ```sh
   python manage.py createsuperuser
   ```

3. **Start the Development Server**:
   ```sh
   python manage.py runserver
   ```

4. **Visit the Site**:
   - Open your browser and go to [http://localhost:8000](http://localhost:8000).

## 🎨 Features 🎨

- **Relive the Past**: Submit your graduation year and explore the events, news, and cultural moments from that time.
- **Submit Facts**: Users can submit facts about the 90s, which are reviewed by admins.
- **Admin Dashboard**: Admins can review, approve, or deny submitted facts.

## 📚 Technologies Used 📚

- **Django**: The web framework for perfectionists with deadlines.
- **Postgres**: The powerful open-source database system.
- **HTML/CSS/JS**: For the nostalgic front-end experience.

## 📞 Support 📞

If you encounter any issues or have questions, feel free to make a pull request.

---