# .env.example - Copy this to .env and fill in your values

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-super-secret-key-change-in-production

# Database Configuration
VECTOR_DB_PATH=healthcare_vectordb

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216  # 16MB in bytes

# AI Model Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MEMORY_WINDOW=10
TEMPERATURE=0.1
LLM_MODEL=gpt-3.5-turbo-instruct
EMBEDDING_MODEL=text-embedding-ada-002

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=healthcare_ai.log

# Optional: Enhanced Features Configuration
# Uncomment if using enhanced version with authentication

# JWT Configuration
# JWT_SECRET_KEY=your-jwt-secret-key
# JWT_EXPIRATION_HOURS=24

# Email Configuration (for notifications)
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your_email@gmail.com
# SMTP_PASSWORD=your_app_password

# Security Configuration
# MAX_LOGIN_ATTEMPTS=5
# LOCKOUT_DURATION_MINUTES=30

# Analytics Configuration
# RETENTION_DAYS=365
# ENABLE_DETAILED_LOGGING=True