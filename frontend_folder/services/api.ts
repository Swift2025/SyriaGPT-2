// src/services/api.ts
import { jwtDecode } from 'jwt-decode';

// تأكد من تثبيت المكتبة: npm install jwt-decode

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9000';

// دالة مساعدة لمعالجة استجابات API بشكل موحد
const handleResponse = async (response: Response) => {
  // حالة خاصة: إذا كان الرد ناجحاً ولكن لا يوجد محتوى (e.g., 204 No Content)
  if (response.status === 204) {
    return;
  }
  
  try {
    const data = await response.json();
    if (!response.ok) {
      let errorMessage = data.message || data.detail || data.error || 'An unknown error occurred.';
      
      // إذا كان errorMessage كائن، حوله إلى نص
      if (typeof errorMessage === 'object') {
        errorMessage = JSON.stringify(errorMessage);
      }
      
      throw new Error(errorMessage);
    }
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Failed to parse response');
  }
};

// دالة لتجديد التوكن
const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) throw new Error("No refresh token available");

  const response = await fetch(`${API_BASE_URL}/sessions/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  const data = await handleResponse(response);

  // إذا نجح التجديد، قم بتحديث التوكنات
  localStorage.setItem('accessToken', data.access_token);
  // قد تعيد الواجهة الخلفية refresh token جديد أيضاً
  if (data.refresh_token) {
    localStorage.setItem('refreshToken', data.refresh_token);
  }
  
  return data.access_token;
};

// دالة للتحقق من صلاحية التوكن وتجديده إذا لزم الأمر
const getValidAccessToken = async () => {
  if (typeof window === 'undefined') return null;
  
  let token = localStorage.getItem('accessToken');
  if (!token) return null;

  try {
    const decoded: { exp: number } = jwtDecode(token);
    // التحقق قبل دقيقة واحدة من انتهاء الصلاحية
    const isExpired = Date.now() >= decoded.exp * 1000 - 60000; 

    if (isExpired) {
      console.log("Access token expired or expiring soon, refreshing...");
      token = await refreshToken();
    }
    return token;
  } catch (error) {
    console.error("Invalid token, attempting refresh:", error);
    // إذا كان التوكن الحالي غير صالح، حاول تجديده
    try {
      token = await refreshToken();
      return token;
    } catch (refreshError) {
      console.error("Failed to refresh token:", refreshError);
      // إذا فشل التجديد، قم بتسجيل الخروج
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      return null;
    }
  }
};

// Interceptor: دالة fetch مخصصة تقوم بالتحقق من التوكن قبل كل طلب
export const apiFetch = async (url: string, options: RequestInit = {}) => {
  const token = await getValidAccessToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });
  return handleResponse(response);
};

// ========================================================================
// AUTHENTICATION ENDPOINTS (/auth)
// ========================================================================

export const loginUser = async (email: string, password: string) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await handleResponse(response);
  
  if (data.data?.access_token) localStorage.setItem('accessToken', data.data.access_token);
  if (data.data?.refresh_token) localStorage.setItem('refreshToken', data.data.refresh_token);
  
  return data;
};

export const registerUser = (userData: { email: string; password: string; first_name: string; last_name: string; phone_number?: string }) => 
  apiFetch('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(userData) });

export const verifyEmail = (token: string) => 
  apiFetch(`/api/v1/auth/verify-email/${token}`);

export const forgotPassword = (email: string) => 
  apiFetch('/api/v1/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) });

export const resetPassword = (token: string, new_password: string, confirm_password: string) => 
  apiFetch('/api/v1/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, new_password, confirm_password }) });

export const getCurrentUser = () => 
  apiFetch('/api/v1/auth/me');

export const getGoogleAuthUrl = (lang: string = 'en') => {
  const frontendCallback = `${window.location.origin}/${lang}/auth/oauth/google/callback`;
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9000';
  
  return fetch(`${API_BASE_URL}/api/v1/auth/oauth/google/authorize`, { 
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      redirect_uri: frontendCallback
    })
  }).then(response => response.json());
};

export const getOAuthProviders = () => 
  apiFetch('/api/v1/auth/oauth/providers');

export const oauthCallback = (provider: string, code: string, state?: string) => 
  apiFetch(`/api/v1/auth/oauth/${provider}/callback`, { method: 'POST', body: JSON.stringify({ code, state }) });

// ========================================================================
// USER MANAGEMENT & SETTINGS
// ========================================================================

export const getUserProfile = () => 
  apiFetch('/api/v1/users/me');

export const updateUserProfile = (profileData: { first_name?: string; last_name?: string; phone_number?: string; profile_picture?: string }) => 
  apiFetch('/api/v1/users/me', { method: 'PUT', body: JSON.stringify(profileData) });

export const changePassword = (passwordData: { current_password: string; new_password: string; confirm_password: string }) => 
  apiFetch('/api/v1/auth/change-password', { method: 'POST', body: JSON.stringify(passwordData) });

export const deleteAccount = () => 
  apiFetch('/api/v1/users/me', { method: 'DELETE' });

export const getUserSettings = () => 
  apiFetch('/api/v1/users/me/settings');

export const updateUserSettings = (settingsData: any) => 
  apiFetch('/api/v1/users/me/settings', { method: 'PUT', body: JSON.stringify(settingsData) });

export const uploadProfilePicture = (file: File) => {
  const formData = new FormData();
  formData.append('profile_picture', file);
  
  return apiFetch('/api/v1/users/me/profile-picture', { 
    method: 'POST', 
    body: formData,
    headers: {} // Remove Content-Type to let browser set it with boundary
  });
};

// ========================================================================
// INTELLIGENT Q&A & CHAT
// ========================================================================

export const askQuestion = (question: string, language: string = 'auto') => 
  apiFetch(`/api/v1/chat/ask?question=${encodeURIComponent(question)}&language=${language}`, { method: 'POST' });

export const getChats = async () => {
  const data = await apiFetch('/api/v1/chat/');
  return data.data || data;
};

export const createChat = (chatData: { title?: string; description?: string; context?: string; language?: string }) => 
  apiFetch('/api/v1/chat/', { method: 'POST', body: JSON.stringify(chatData) });

export const getChat = (chatId: string) => 
  apiFetch(`/api/v1/chat/${chatId}`);

export const updateChat = (chatId: string, chatData: { title?: string; description?: string; context?: string; language?: string }) => 
  apiFetch(`/api/v1/chat/${chatId}`, { method: 'PUT', body: JSON.stringify(chatData) });

export const deleteChat = (chatId: string) => 
  apiFetch(`/api/v1/chat/${chatId}`, { method: 'DELETE' });

export const sendMessage = (chatId: string, messageData: { message: string; message_type?: string; attachments?: any[] }) => 
  apiFetch(`/api/v1/chat/${chatId}/messages`, { method: 'POST', body: JSON.stringify(messageData) });

export const getChatMessages = (chatId: string, page: number = 1, limit: number = 50) => 
  apiFetch(`/api/v1/chat/${chatId}/messages?page=${page}&limit=${limit}`);

export const deleteMessage = (chatId: string, messageId: string) => 
  apiFetch(`/api/v1/chat/${chatId}/messages/${messageId}`, { method: 'DELETE' });

export const clearChatHistory = async (chatIds: string[] = []) => {
  // Check if user is authenticated first
  const token = localStorage.getItem('accessToken');
  if (!token) {
    throw new Error('غير مسجل دخول. يرجى تسجيل الدخول أولاً.');
  }
  
  // If no chat IDs provided, get all user's chats first
  if (chatIds.length === 0) {
    try {
      const chatsResponse = await apiFetch('/chat/');
      const allChats = chatsResponse.data?.chats || [];
      chatIds = allChats.map((chat: any) => chat.id);
    } catch (error: any) {
      console.error('Error fetching chats for deletion:', error);
      
      // Handle specific authentication errors
      if (error.message?.includes('Not authenticated') || error.message?.includes('401')) {
        throw new Error('انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى.');
      } else if (error.message?.includes('403') || error.message?.includes('Forbidden')) {
        throw new Error('ليس لديك صلاحية للوصول إلى المحادثات.');
      } else {
        throw new Error('فشل في جلب المحادثات للحذف');
      }
    }
  }
  
  // If still no chats, return success message
  if (chatIds.length === 0) {
    return {
      message: "لا توجد محادثات للحذف",
      success_count: 0,
      failed_count: 0
    };
  }
  
  return apiFetch('/chat/bulk-action', { 
    method: 'POST', 
    body: JSON.stringify({ chat_ids: chatIds, action: 'delete' }) 
  });
};

export const exportChat = (chatId: string, format: string = 'json') => 
  apiFetch(`/chat/${chatId}/export`, { method: 'POST', body: JSON.stringify({ format }) });

export const exportUserData = () => 
  apiFetch('/users/me/export', { method: 'POST', body: JSON.stringify({ format: 'json' }) });

export const addFeedbackToMessage = async (messageId: string, feedbackData: { rating: number; feedback_type: string; comment?: string }) => {
  return apiFetch(`/chat/messages/${messageId}/feedback`, {
    method: 'POST',
    body: JSON.stringify(feedbackData),
  });
};

export const regenerateResponse = async (chatId: string, lastUserMessage: string) => {
  return sendMessage(chatId, { message: lastUserMessage });
};

// ========================================================================
// SESSION MANAGEMENT
// ========================================================================

export const createSession = (sessionData: { user_id: string; expires_at?: string }) => 
  apiFetch('/sessions/', { method: 'POST', body: JSON.stringify(sessionData) });

export const getSession = (sessionId: string) => 
  apiFetch(`/sessions/${sessionId}`);

export const updateSession = (sessionId: string, sessionData: { expires_at?: string; is_active?: boolean }) => 
  apiFetch(`/sessions/${sessionId}`, { method: 'PUT', body: JSON.stringify(sessionData) });

export const deleteSession = (sessionId: string) => 
  apiFetch(`/sessions/${sessionId}`, { method: 'DELETE' });

export const getUserSessions = () => 
  apiFetch('/sessions/user');

// ========================================================================
// QUESTIONS & ANSWERS
// ========================================================================

export const getQuestions = (page: number = 1, limit: number = 20, search?: string) => {
  const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
  if (search) params.append('search', search);
  return apiFetch(`/questions/?${params.toString()}`);
};

export const getQuestion = (questionId: string) => 
  apiFetch(`/questions/${questionId}`);

export const createQuestion = (questionData: { title: string; content: string; category?: string; tags?: string[] }) => 
  apiFetch('/questions/', { method: 'POST', body: JSON.stringify(questionData) });

export const updateQuestion = (questionId: string, questionData: { title?: string; content?: string; category?: string; tags?: string[] }) => 
  apiFetch(`/questions/${questionId}`, { method: 'PUT', body: JSON.stringify(questionData) });

export const deleteQuestion = (questionId: string) => 
  apiFetch(`/questions/${questionId}`, { method: 'DELETE' });

export const getAnswers = (questionId: string, page: number = 1, limit: number = 20) => 
  apiFetch(`/questions/${questionId}/answers?page=${page}&limit=${limit}`);

export const createAnswer = (questionId: string, answerData: { content: string; is_ai_generated?: boolean }) => 
  apiFetch(`/questions/${questionId}/answers`, { method: 'POST', body: JSON.stringify(answerData) });

export const updateAnswer = (answerId: string, answerData: { content: string }) => 
  apiFetch(`/answers/${answerId}`, { method: 'PUT', body: JSON.stringify(answerData) });

export const deleteAnswer = (answerId: string) => 
  apiFetch(`/answers/${answerId}`, { method: 'DELETE' });

// ========================================================================
// SMTP & EMAIL
// ========================================================================

export const getSmtpProviders = () => 
  apiFetch('/smtp/providers');

export const testSmtpConnection = (providerData: { provider: string; config: any }) => 
  apiFetch('/smtp/test', { method: 'POST', body: JSON.stringify(providerData) });

export const sendTestEmail = (emailData: { to: string; subject: string; body: string }) => 
  apiFetch('/smtp/send-test', { method: 'POST', body: JSON.stringify(emailData) });

// ========================================================================
// FILE UPLOADS
// ========================================================================

export const uploadFile = (file: File, type: string = 'general') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);
  
  return apiFetch('/files/upload', { 
    method: 'POST', 
    body: formData,
    headers: {} // Remove Content-Type to let browser set it with boundary
  });
};

export const getFiles = (type?: string, page: number = 1, limit: number = 20) => {
  const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
  if (type) params.append('type', type);
  return apiFetch(`/files/?${params.toString()}`);
};

export const deleteFile = (fileId: string) => 
  apiFetch(`/files/${fileId}`, { method: 'DELETE' });

// ========================================================================
// UTILITY FUNCTIONS
// ========================================================================


// ========================================================================
// ERROR HANDLING & LOGGING
// ========================================================================

export const logError = (errorData: { level: string; message: string; context?: any }) => 
  apiFetch('/logs/error', { method: 'POST', body: JSON.stringify(errorData) });

export const getErrorLogs = (page: number = 1, limit: number = 50, level?: string) => {
  const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
  if (level) params.append('level', level);
  return apiFetch(`/logs/errors?${params.toString()}`);
};