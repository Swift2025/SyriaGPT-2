# SyriaGPT 🤖

**Intelligent Q&A System for Syria-related Questions Powered by Google Gemini AI**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-3.9-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis)](https://redis.io/)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.15-FF6B6B?style=flat-square)](https://qdrant.tech/)

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Authentication Guide](#authentication-guide)
- [Data Sources](#data-sources)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

SyriaGPT is an intelligent question-answering system specifically designed to provide accurate, comprehensive, and contextually relevant information about Syria. The system leverages advanced AI technologies including Google Gemini, vector search, and semantic understanding to deliver high-quality responses to user queries.

### Key Capabilities

- **Intelligent Q&A**: Advanced question processing with semantic understanding
- **Multi-language Support**: English and Arabic language support
- **Vector Search**: Semantic similarity search using Qdrant vector database
- **Caching System**: Redis-based caching for improved performance
- **User Authentication**: Complete user management with OAuth support
- **Session Management**: Persistent user sessions and conversation history
- **Real-time Processing**: Fast response times with intelligent caching

## ✨ Features

### 🤖 AI-Powered Q&A
- **Google Gemini Integration**: State-of-the-art AI model for answer generation
- **Semantic Search**: Vector-based similarity search for relevant information
- **Context Awareness**: Maintains conversation context for better responses
- **Quality Assessment**: Confidence scoring for answer reliability

### 🔐 Authentication & Security
- **User Registration/Login**: Complete user management system
- **OAuth Integration**: Social login support (Google)
- **Two-Factor Authentication**: Enhanced security with TOTP
- **Password Recovery**: Secure password reset functionality
- **Email Verification**: Account verification via email
- **Dynamic SMTP Configuration**: Support for multiple email providers (Gmail, Hotmail, Outlook, Yahoo, etc.)

### 📊 Data Management
- **Comprehensive Knowledge Base**: Extensive Syria-related data
- **Vector Database**: Qdrant for semantic search capabilities
- **Caching Layer**: Redis for performance optimization
- **Session Storage**: Persistent user sessions and history

### 🌐 API Features
- **RESTful API**: Clean, documented API endpoints
- **Real-time Processing**: Fast response times
- **Health Monitoring**: System health checks and monitoring
- **Error Handling**: Comprehensive error management

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │     Redis       │
│   (Port 9000)   │◄──►│   (Port 5432)   │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Qdrant        │    │   Google Gemini │    │   Email Service │
│   (Port 6333)   │    │   API           │    │   (SMTP)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Processing Pipeline

1. **Input Normalization** → Question preprocessing and standardization
2. **Cache Check** → Redis lookup for existing answers
3. **Semantic Search** → Qdrant vector similarity search
4. **Quality Evaluation** → Confidence scoring and validation
5. **AI Generation** → Google Gemini API for new answers
6. **Storage** → Multi-system persistence (PostgreSQL, Redis, Qdrant)

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI 0.116.1**: Modern, fast web framework for building APIs
- **Python 3.13**: Latest Python version for optimal performance
- **Uvicorn**: ASGI server for running FastAPI applications

### Database & Storage
- **PostgreSQL 15**: Primary relational database
- **Redis 7**: In-memory caching and session storage
- **Qdrant 1.15**: Vector database for semantic search

### AI & Machine Learning
- **Google Gemini**: Advanced AI model for answer generation
- **Vector Embeddings**: Semantic representation of text
- **Similarity Search**: Vector-based information retrieval

### Authentication & Security
- **JWT Tokens**: Secure authentication mechanism
- **OAuth 2.0**: Social login integration
- **TOTP**: Two-factor authentication
- **bcrypt**: Password hashing

### Development & Deployment
- **Docker & Docker Compose**: Containerized deployment
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization
- **SQLAlchemy**: ORM for database operations

## 📋 Prerequisites

Before setting up SyriaGPT, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Python 3.13** (for local development)
- **Git** (for version control)

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 10GB free space
- **CPU**: Multi-core processor recommended
- **Network**: Internet connection for AI API calls

## 🚀 Installation & Setup

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SyriaGPT
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - **API**: http://localhost:9000
   - **API Documentation**: http://localhost:9000/docs
   - **PgAdmin**: http://localhost:5050 (admin@admin.com / admin123)

### Local Development Setup

1. **Clone and navigate to project**
   ```bash
   git clone <repository-url>
   cd SyriaGPT
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Configure your .env file
   ```

5. **Start required services**
   ```bash
   docker-compose up -d db redis qdrant
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 9000 --reload
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://admin:admin123@localhost:5432/syriagpt
REDIS_URL=redis://localhost:6379

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
```

### Configuration Files

The application uses several configuration files in the `config/` directory:

- **`messages.json`**: Localized message templates
- **`oauth_providers.json`**: OAuth provider configurations
- **`email_templates.json`**: Email template definitions
- **`smtp_providers.json`**: SMTP provider configurations for dynamic email setup

### SMTP Configuration

The system supports dynamic SMTP configuration for multiple email providers:

#### Supported Providers
- **Gmail**: `smtp.gmail.com:587` (requires App Password)
- **Hotmail/Outlook**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587` (requires App Password)
- **iCloud**: `smtp.mail.me.com:587` (requires App Password)
- **Zoho**: `smtp.zoho.com:587`
- **ProtonMail**: Via Bridge application
- **Custom SMTP**: User-defined servers

#### Environment Variables
```bash
# Email Configuration
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password_or_app_password
EMAIL_FROM=noreply@syriagpt.com
EMAIL_FROM_NAME=Syria GPT

# Optional: Override auto-detection
SMTP_PROVIDER=gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

#### API Endpoints
```http
GET  /smtp/providers              # Get all SMTP providers
GET  /smtp/providers/{provider}   # Get provider details
POST /smtp/test                   # Test SMTP connection
POST /smtp/detect-provider        # Detect provider from email
GET  /smtp/supported-domains      # Get supported domains
POST /smtp/configure              # Configure SMTP settings
GET  /smtp/health                 # SMTP health check
```

For detailed SMTP configuration instructions, see [SMTP_CONFIGURATION_GUIDE.md](SMTP_CONFIGURATION_GUIDE.md).

## 📚 Usage

### API Endpoints

#### Authentication Endpoints

```http
POST /auth/register          # User registration
POST /auth/login             # User login
POST /auth/oauth/{provider}/authorize  # OAuth authorization
GET  /auth/oauth/{provider}/callback   # OAuth callback
POST /auth/forgot-password   # Password recovery
POST /auth/reset-password    # Password reset
POST /auth/2fa/setup         # Two-factor setup
POST /auth/2fa/verify        # Two-factor verification
```

#### Q&A Endpoints

```http
POST /intelligent-qa/ask     # Ask intelligent question
GET  /intelligent-qa/health  # System health check
GET  /questions              # Get user questions
POST /questions              # Create new question
GET  /answers                # Get answers
POST /answers                # Create new answer
```

#### Session Management

```http
GET  /session/current        # Get current session
POST /session/logout         # Logout user
GET  /session/history        # Get session history
```

### Example API Usage

#### Ask a Question

```bash
curl -X POST "http://localhost:9000/intelligent-qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the capital of Syria?",
    "language": "en"
  }'
```

#### User Registration

```bash
curl -X POST "http://localhost:9000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### User Login

```bash
curl -X POST "http://localhost:9000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Web Interface

Access the interactive API documentation at:
- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc

## 🔐 Authentication Guide

For detailed instructions on how to use authentication in Swagger UI, see the [Swagger Authentication Guide](SWAGGER_AUTHENTICATION_GUIDE.md).

### Quick Authentication Steps:
1. **Get a token**: Use `POST /auth/login` with your credentials
2. **Authorize in Swagger**: Click the 🔒 Authorize button and enter `Bearer YOUR_TOKEN`
3. **Test**: Use `GET /auth/me` to verify authentication

## 📊 Data Sources

The system includes comprehensive Syria-related knowledge in the following categories:

### Knowledge Base Structure

```
data/syria_knowledge/
├── cities.json                    # Syrian cities and locations
├── culture.json                   # Cultural information
├── economy.json                   # Economic data
├── general.json                   # General information
├── government.json                # Government and politics
└── Real_post_liberation_events.json  # Post-liberation events
```

### Data Categories

- **Cities**: Geographic information about Syrian cities
- **Culture**: Cultural heritage, traditions, and customs
- **Economy**: Economic indicators, trade, and financial data
- **General**: General facts and information about Syria
- **Government**: Political structure, institutions, and governance
- **Post-Liberation Events**: Historical events and developments

## 🔧 Development

### Project Structure

```
SyriaGPT/
├── api/                          # API endpoints and routes
│   ├── authentication/           # Auth-related endpoints
│   ├── questions/                # Question management
│   ├── answers/                  # Answer management
│   └── ai/                       # AI Q&A endpoints
├── config/                       # Configuration files
├── data/                         # Knowledge base data
├── models/                       # Data models and schemas
├── services/                     # Business logic services
│   ├── ai/                       # AI-related services
│   ├── auth/                     # Authentication services
│   ├── database/                 # Database services
│   └── repositories/             # Data access layer
├── migrations/                   # Database migrations
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker services
└── Dockerfile                    # Docker configuration
```

### Development Commands

```bash
# Run tests
pytest

# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 9000
```

### Adding New Features

1. **Create new API endpoints** in the appropriate `api/` subdirectory
2. **Add business logic** in the `services/` directory
3. **Define data models** in `models/` directory
4. **Update database schema** using Alembic migrations
5. **Add tests** for new functionality
6. **Update documentation** and API docs

## 🚀 Deployment

### Production Deployment

1. **Prepare production environment**
   ```bash
   # Set production environment variables
   export ENVIRONMENT=production
   export DEBUG=False
   ```

2. **Build and deploy with Docker**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Set up reverse proxy** (Nginx recommended)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:9000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Configure SSL** with Let's Encrypt
   ```bash
   certbot --nginx -d your-domain.com
   ```

### Monitoring & Logging

- **Application Logs**: Check container logs with `docker-compose logs -f app`
- **Database Monitoring**: Use PgAdmin at http://localhost:5050
- **Health Checks**: Monitor `/intelligent-qa/health` endpoint
- **Performance**: Monitor response times and cache hit rates

### Scaling Considerations

- **Horizontal Scaling**: Use multiple application instances behind a load balancer
- **Database Scaling**: Consider read replicas for PostgreSQL
- **Cache Scaling**: Use Redis Cluster for high availability
- **Vector Database**: Scale Qdrant with multiple nodes

## 🤝 Contributing

We welcome contributions to SyriaGPT! Please follow these guidelines:

### Contribution Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines

- **Code Style**: Follow PEP 8 and use Black for formatting
- **Testing**: Write tests for new features and ensure all tests pass
- **Documentation**: Update documentation for new features
- **Type Hints**: Use type hints for all function parameters and return values
- **Error Handling**: Implement proper error handling and logging

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Follow the project's coding standards
- Test your changes thoroughly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini**: For providing the AI capabilities
- **FastAPI**: For the excellent web framework
- **Qdrant**: For the vector database technology
- **Open Source Community**: For the various libraries and tools used

## 📞 Support

For support and questions:

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the API docs at `/docs`
- **Email**: Contact the development team

---

**Made with ❤️ for Syria and its people**
