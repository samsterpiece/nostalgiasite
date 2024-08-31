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
   ```

2. **Create and Activate Virtual Environment**:
   - On Windows:
     ```sh
     python -m venv venv
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```sh
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Python Requirements**:
   ```sh
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Ensure you have the necessary environment variables set up in your `.env` file:
     ```
     DATABASE_URL=postgres://username:password@localhost:5432/nostalgia_db
     SECRET_KEY=your_secret_key
     DEBUG=True
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

### 🚀 Running the Application 🚀

1. **Navigate to the Directory Containing manage.py**:
   ```sh
   cd path/to/directory/containing/manage.py
   ```

2. **Migrate the Database**:
   ```sh
   python manage.py migrate
   ```

3. **Create a Superuser (Optional)**:
   ```sh
   python manage.py createsuperuser
   ```

4. **Start the Development Server**:
   ```sh
   python manage.py runserver
   ```

5. **Visit the Site**:
   - Open your browser and go to [http://localhost:8000](http://localhost:8000).

## 🛠️ Git Configuration

To avoid issues with line endings, configure Git as follows:

1. Add `venv/` to your `.gitignore` file to exclude the virtual environment from version control.

2. Configure Git's line ending behavior:
   - On Windows:
     ```
     git config --global core.autocrlf true
     ```
   - On macOS or Linux:
     ```
     git config --global core.autocrlf input
     ```

3. Create a `.gitattributes` file in the root of your repository with the following content:
   ```
   * text=auto
   *.py text
   *.js text
   *.html text
   *.css text
   *.md text
   *.sln text eol=crlf
   *.png binary
   *.jpg binary
   ```

These steps will ensure consistent line endings across different operating systems and prevent warnings during Git operations.

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
