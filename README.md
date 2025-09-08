# SyriaGPT - AI Chatbot System

A sophisticated FastAPI-based AI chatbot system that provides intelligent Q&A capabilities about Syria, with advanced features including authentication, vector search, chat management, and email systems.

## 🚀 Features

### Core Features
- **🤖 AI Integration**: Google Gemini AI for intelligent responses about Syria
- **🔐 Authentication**: JWT-based auth with OAuth (Google), 2FA, email verification
- **🔍 Vector Search**: Qdrant vector database for semantic search
- **💬 Chat Management**: Persistent chat sessions with message history
- **📧 Email System**: Dynamic SMTP configuration with multiple providers
- **🗄️ Database**: PostgreSQL with Alembic migrations
- **📊 Logging**: Comprehensive structured logging system
- **🐳 Docker Support**: Full containerization with docker-compose

### Advanced Features
- **Multilingual Support**: Arabic and English language support
- **Context-Aware Responses**: Intelligent Q&A about Syria with context
- **Question Variant Generation**: Generate multiple ways to ask questions
- **News Integration**: Web scraping and news integration
- **User Management**: Complete user profile and preference management
- **Session Management**: Secure session handling with refresh tokens
- **Rate Limiting**: Built-in rate limiting for API protection
- **Health Monitoring**: Comprehensive health checks for all services

## 📁 Project Structure

```
SyriaGPT-2/
├── main.py                          # Main FastAPI application
├── requirements.txt                 # Python dependencies
├── docker-compose.yml              # Docker services configuration
├── Dockerfile                      # Docker image configuration
├── alembic.ini                     # Alembic configuration
├── env.example                     # Environment variables template
├── README.md                       # This file
├── api/                           # API routes and endpoints
│   ├── authentication/            # Authentication endpoints
│   ├── ai/                        # AI and chat endpoints
│   ├── session/                   # Session management
│   ├── smtp/                      # SMTP configuration
│   └── user_management/           # User management
├── config/                        # Configuration files
│   ├── config_loader.py           # Configuration management
│   ├── logging_config.py          # Logging configuration
│   ├── messages.json              # System messages
│   ├── oauth_providers.json       # OAuth provider configs
│   ├── smtp_providers.json        # SMTP provider configs
│   ├── email_templates.json       # Email templates
│   └── identity_responses.json    # AI identity responses
├── data/                          # Knowledge base data
│   └── syria_knowledge/           # Syria-specific knowledge
├── logs/                          # Application logs
├── migrations/                    # Database migrations
├── models/                        # Database models and schemas
│   ├── domain/                    # SQLAlchemy models
│   └── schemas/                   # Pydantic schemas
└── services/                      # Business logic services
    ├── ai/                        # AI and ML services
    ├── auth/                      # Authentication services
    ├── database/                  # Database services
    ├── email/                     # Email services
    └── repositories/              # Data access layer
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional)
- Docker & Docker Compose (for containerized deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SyriaGPT-2
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
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb syriagpt
   
   # Run migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Clone and navigate to project**
   ```bash
   git clone <repository-url>
   cd SyriaGPT-2
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec syriagpt alembic upgrade head
   ```

## ⚙️ Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following:

#### Database Configuration
```env
DATABASE_URL=postgresql+psycopg2://admin:admin123@localhost:5432/syriagpt
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=syriagpt
DATABASE_USER=admin
DATABASE_PASSWORD=admin123
```

#### Security Configuration
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### Google AI Configuration
```env
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

#### OAuth Configuration
```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:9000/auth/google/callback
```

#### Qdrant Vector Database
```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=syria_qa_vectors
QDRANT_API_KEY=your-qdrant-api-key
EMBEDDING_DIM=768
```

#### Email Configuration
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM_NAME=SyriaGPT
EMAIL_FROM_ADDRESS=noreply@syriagpt.com
```

### Configuration Files

The system uses JSON configuration files in the `config/` directory:

- **`messages.json`**: System messages in Arabic and English
- **`oauth_providers.json`**: OAuth provider configurations
- **`smtp_providers.json`**: SMTP provider configurations
- **`email_templates.json`**: Email template configurations
- **`identity_responses.json`**: AI identity and response templates

## 🔧 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "confirm_password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "language_preference": "ar"
}
```

#### Login User
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "remember_me": false,
  "two_factor_code": "123456"
}
```

#### OAuth Login
```http
GET /auth/oauth/google
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

### Chat Endpoints

#### Create Chat
```http
POST /chat/
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "title": "My Chat",
  "description": "Chat about Syria",
  "ai_model": "gemini-pro",
  "language": "ar",
  "max_tokens": 2048,
  "temperature": "0.7"
}
```

#### Send Message
```http
POST /chat/{chat_id}/messages
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "content": "What is the capital of Syria?",
  "role": "user",
  "message_type": "text"
}
```

### Intelligent Q&A Endpoints

#### Ask Question
```http
POST /intelligent-qa/ask
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "question": "What is the history of Damascus?",
  "language": "ar",
  "include_sources": true,
  "max_results": 5
}
```

#### Generate Question Variants
```http
POST /intelligent-qa/variants
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "question": "What is the capital of Syria?",
  "language": "ar",
  "num_variants": 3
}
```

### User Management Endpoints

#### Get User Profile
```http
GET /user/profile
Authorization: Bearer your-access-token
```

#### Update User Profile
```http
PUT /user/profile
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "username": "new_username",
  "first_name": "New Name",
  "bio": "Updated bio"
}
```

### Health Check Endpoints

#### Basic Health Check
```http
GET /health
```

#### Detailed Health Check
```http
GET /health/detailed
```

## 🗄️ Database Schema

### Users Table
- User authentication and profile information
- OAuth integration fields
- Two-factor authentication settings
- Preferences and notification settings

### Chats Table
- Chat sessions with AI models
- Chat settings and metadata
- Message count and token usage

### Chat Messages Table
- Individual messages in chats
- Message types (text, image, file, etc.)
- AI processing metadata

### User Sessions Table
- JWT session management
- Session security and device information
- Session expiration and revocation

### QA Pairs Table
- Question-answer pairs for knowledge base
- Vector embeddings for semantic search
- Source attribution and quality ratings

## 🔐 Security Features

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- OAuth integration (Google, Facebook, GitHub, etc.)
- Two-factor authentication with TOTP
- Email verification system
- Password strength validation

### Session Management
- Secure session handling
- Session revocation and cleanup
- Device and location tracking
- Session timeout management

### Data Protection
- Password hashing with bcrypt
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting

## 📊 Monitoring & Logging

### Logging System
- Structured logging with JSON format
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log rotation and file management
- Colored console output for development

### Health Monitoring
- Service health checks
- Database connectivity monitoring
- External service monitoring
- Performance metrics

### Error Handling
- Comprehensive error handling
- Structured error responses
- Error logging and tracking
- Graceful degradation

## 🚀 Deployment

### Production Deployment

1. **Set up production environment**
   ```bash
   # Set production environment variables
   export ENVIRONMENT=production
   export DEBUG=false
   export LOG_LEVEL=INFO
   ```

2. **Use production database**
   ```bash
   # Update DATABASE_URL for production
   export DATABASE_URL=postgresql+psycopg2://user:pass@prod-db:5432/syriagpt
   ```

3. **Configure reverse proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:9000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Set up SSL certificates**
   ```bash
   # Using Let's Encrypt
   certbot --nginx -d your-domain.com
   ```

### Docker Production Deployment

1. **Use production docker-compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Set up monitoring**
   ```bash
   # Add monitoring services
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py
```

### Test Structure
```
tests/
├── test_auth.py              # Authentication tests
├── test_chat.py              # Chat functionality tests
├── test_ai.py                # AI service tests
├── test_user_management.py   # User management tests
└── conftest.py               # Test configuration
```

## 📈 Performance Optimization

### Database Optimization
- Connection pooling
- Query optimization
- Index optimization
- Caching strategies

### API Optimization
- Response caching
- Pagination
- Rate limiting
- Async processing

### AI Service Optimization
- Embedding caching
- Vector search optimization
- Model optimization
- Batch processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use type hints
- Follow security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- API Documentation: `http://localhost:9000/docs`
- ReDoc Documentation: `http://localhost:9000/redoc`

### Getting Help
- Check the [Issues](https://github.com/your-repo/issues) page
- Create a new issue for bugs or feature requests
- Join our community discussions

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
psql -h localhost -U admin -d syriagpt

# Reset database
dropdb syriagpt && createdb syriagpt
alembic upgrade head
```

#### Email Configuration Issues
```bash
# Test SMTP configuration
python -c "
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('your-email@gmail.com', 'your-app-password')
print('SMTP connection successful')
smtp.quit()
"
```

#### OAuth Configuration Issues
- Verify OAuth credentials in environment variables
- Check redirect URIs in OAuth provider settings
- Ensure OAuth provider is enabled in configuration

## 🎯 Roadmap

### Upcoming Features
- [ ] Advanced AI model support
- [ ] Real-time chat with WebSockets
- [ ] Mobile app integration
- [ ] Advanced analytics dashboard
- [ ] Multi-tenant support
- [ ] API rate limiting improvements
- [ ] Advanced caching strategies
- [ ] Machine learning model training

### Version History
- **v2.0.0**: Complete rewrite with FastAPI, advanced features
- **v1.0.0**: Initial release with basic functionality

---

**SyriaGPT** - Intelligent Q&A System for Syria 🇸🇾

Built with ❤️ using FastAPI, PostgreSQL, and Google AI
