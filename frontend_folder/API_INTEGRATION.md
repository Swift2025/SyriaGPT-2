# SyriaGPT Frontend API Integration

This document describes the complete API integration implemented in the SyriaGPT frontend application.

## Overview

The frontend has been fully integrated with all backend endpoints, providing a comprehensive chat experience with authentication, file management, and advanced features.

## API Service (`services/api.ts`)

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user
- `POST /auth/verify-email/{token}` - Verify email
- `POST /auth/forgot-password` - Forgot password
- `POST /auth/reset-password` - Reset password
- `POST /auth/oauth/{provider}/authorize` - OAuth authorization
- `GET /auth/oauth/providers` - Get OAuth providers

### User Management
- `GET /users/me/profile` - Get user profile
- `PUT /users/me/profile` - Update user profile
- `POST /users/me/change-password` - Change password
- `DELETE /users/me/profile` - Delete account
- `GET /users/me/settings` - Get user settings
- `PUT /users/me/settings` - Update user settings
- `POST /users/me/profile/picture` - Upload profile picture

### Chat Management
- `GET /chat/` - Get all chats
- `POST /chat/` - Create new chat
- `GET /chat/{chatId}` - Get specific chat
- `PUT /chat/{chatId}` - Update chat
- `DELETE /chat/{chatId}` - Delete chat
- `POST /chat/{chatId}/messages` - Send message
- `GET /chat/{chatId}/messages` - Get chat messages
- `DELETE /chat/{chatId}/messages/{messageId}` - Delete message
- `POST /chat/bulk-action` - Bulk chat operations
- `POST /chat/{chatId}/export` - Export chat

### Intelligent Q&A
- `POST /intelligent-qa/ask` - Ask question
- `POST /chat/messages/{messageId}/feedback` - Add message feedback

### Session Management
- `POST /sessions/` - Create session
- `GET /sessions/{sessionId}` - Get session
- `PUT /sessions/{sessionId}` - Update session
- `DELETE /sessions/{sessionId}` - Delete session
- `GET /sessions/user` - Get user sessions

### Questions & Answers
- `GET /questions/` - Get questions
- `GET /questions/{questionId}` - Get specific question
- `POST /questions/` - Create question
- `PUT /questions/{questionId}` - Update question
- `DELETE /questions/{questionId}` - Delete question
- `GET /questions/{questionId}/answers` - Get answers
- `POST /questions/{questionId}/answers` - Create answer
- `PUT /answers/{answerId}` - Update answer
- `DELETE /answers/{answerId}` - Delete answer

### File Management
- `POST /files/upload` - Upload file
- `GET /files/` - Get files
- `DELETE /files/{fileId}` - Delete file

### SMTP & Email
- `GET /smtp/providers` - Get SMTP providers
- `POST /smtp/test` - Test SMTP connection
- `POST /smtp/send-test` - Send test email

### Utility Endpoints
- `GET /health` - Health check
- `GET /system/info` - System information
- `GET /version` - API version
- `POST /logs/error` - Log error
- `GET /logs/errors` - Get error logs

## Key Features Implemented

### 1. Authentication & Authorization
- JWT token management with automatic refresh
- Protected routes and components
- User session management
- OAuth integration support

### 2. Chat Functionality
- Real-time chat interface
- Message history and persistence
- File attachments support
- Message feedback system
- Chat export functionality
- Chat archiving and management

### 3. File Management
- Drag & drop file uploads
- Multiple file type support
- File size validation
- Progress indicators
- File preview and download

### 4. Advanced Features
- Speech recognition for voice input
- Dark/light theme switching
- Multi-language support
- Responsive design
- Real-time notifications

### 5. User Experience
- Loading states and skeletons
- Error handling and user feedback
- Smooth animations and transitions
- Accessibility features
- Mobile-responsive design

## Environment Configuration

Create a `.env.local` file with the following variables:

```bash
# API Configuration
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_FILE_UPLOAD_ENABLED=true
NEXT_PUBLIC_SPEECH_RECOGNITION_ENABLED=true
NEXT_PUBLIC_OAUTH_ENABLED=true
```

## Usage Examples

### Creating a New Chat
```typescript
import { createChat } from '../services/api';

const newChat = await createChat({
  title: 'New Conversation',
  description: 'Starting a new chat session'
});
```

### Sending a Message
```typescript
import { sendMessage } from '../services/api';

const response = await sendMessage(chatId, {
  message: 'Hello, how are you?',
  attachments: [fileId1, fileId2]
});
```

### File Upload
```typescript
import { uploadFile } from '../services/api';

const fileResult = await uploadFile(file, 'chat');
```

## Error Handling

The API service includes comprehensive error handling:
- Network error detection
- Token expiration handling
- Automatic retry mechanisms
- User-friendly error messages
- Toast notifications for feedback

## Security Features

- JWT token validation
- Automatic token refresh
- Secure file uploads
- Input sanitization
- XSS protection
- CSRF protection

## Performance Optimizations

- Lazy loading of components
- Efficient state management
- Optimized re-renders
- Debounced search
- Pagination for large datasets
- Image optimization

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers support
- Progressive Web App features
- Offline capability support

## Testing

The frontend includes:
- Unit tests for components
- Integration tests for API calls
- E2E tests for user flows
- Accessibility testing
- Performance testing

## Deployment

The application is ready for deployment with:
- Docker containerization
- Environment-specific configurations
- Build optimization
- Static asset optimization
- CDN integration support

## Support

For technical support or questions about the API integration, please refer to the backend API documentation or contact the development team.
