// src/services/api.ts 
import { jwtDecode } from 'jwt-decode';

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

const handleResponse = async (response: Response) => {
  if (response.status === 204) return;
  const data = await response.json();
  if (!response.ok) {
    const errorMessage = data.message || data.detail || 'An unknown error occurred.';
    throw new Error(errorMessage);
  }
  return data;
};

const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) throw new Error("No refresh token available");

  const response = await fetch(`${API_BASE_URL}/sessions/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  const data = await handleResponse(response);
  // --- تعديل مهم: refreshToken الآن فقط يرجع التوكن الجديد ---
  // AuthContext سيكون مسؤولاً عن حفظه
  localStorage.setItem('accessToken', data.access_token);
  if (data.refresh_token) {
    localStorage.setItem('refreshToken', data.refresh_token);
  }
  return data.access_token;
};

const getValidAccessToken = async () => {
  if (typeof window === 'undefined') return null;
  let token = localStorage.getItem('accessToken');
  if (!token) return null;

  try {
    const decoded: { exp: number } = jwtDecode(token);
    const isExpired = Date.now() >= decoded.exp * 1000 - 60000;
    if (isExpired) {
      token = await refreshToken();
    }
    return token;
  } catch (error) {
    try {
      token = await refreshToken();
      return token;
    } catch (refreshError) {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      return null;
    }
  }
};

const apiFetch = async (url: string, options: RequestInit = {}) => {
  const token = await getValidAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const fullUrl = `${API_BASE_URL}${url}`;
  const response = await fetch(fullUrl, { ...options, headers });
  return handleResponse(response);
};
// ========================================================================
// AUTHENTICATION
// ========================================================================

export const loginUser = async (email: string, password: string, remember_me: boolean = false, two_factor_code?: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, remember_me, two_factor_code }),
  });
  return handleResponse(response);
};

export const registerUser = async (userData: {
  email: string;
  password: string;
  phone_number?: string;
  first_name?: string;
  last_name?: string;
}) => {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });
  return handleResponse(response);
};

export const verifyEmail = async (token: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/verify-email/${token}`, {
    method: 'GET',
  });
  return handleResponse(response);
};

export const forgotPassword = async (email: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  return handleResponse(response);
};

export const resetPassword = async (token: string, new_password: string, confirm_password: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password, confirm_password }),
  });
  return handleResponse(response);
};

export const getCurrentUser = () => apiFetch('/auth/me');

// OAuth endpoints
export const getOAuthProviders = async () => {
  const response = await fetch(`${API_BASE_URL}/auth/oauth/providers`, {
    method: 'GET',
  });
  return handleResponse(response);
};

export const getOAuthAuthUrl = async (provider: string, redirect_uri?: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/oauth/${provider}/authorize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, redirect_uri }),
  });
  return handleResponse(response);
};

export const refreshOAuthToken = async (email: string, provider: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/oauth/${provider}/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, provider }),
  });
  return handleResponse(response);
};

// Two-Factor Authentication
export const setup2FA = () => apiFetch('/auth/2fa/setup', { method: 'POST' });
export const verify2FA = (code: string) => apiFetch('/auth/2fa/verify', { 
  method: 'POST', 
  body: JSON.stringify({ code }) 
});
export const disable2FA = () => apiFetch('/auth/2fa/disable', { method: 'POST' });

// ========================================================================
// USER MANAGEMENT
// ========================================================================

export const getUserProfile = () => apiFetch('/users/me/profile');
export const updateUserProfile = (profileData: { 
  first_name?: string; 
  last_name?: string; 
  phone_number?: string; 
  profile_picture?: string;
}) => apiFetch('/users/me/profile', { 
  method: 'PUT', 
  body: JSON.stringify(profileData) 
});

export const getUserSettings = () => apiFetch('/users/me/settings');
export const updateUserSettings = (settingsData: {
  email_notifications?: boolean;
  sms_notifications?: boolean;
  two_factor_enabled?: boolean;
  session_timeout_hours?: number;
  max_concurrent_sessions?: number;
  language?: string;
  timezone?: string;
  theme?: string;
}) => apiFetch('/users/me/settings', { 
  method: 'PUT', 
  body: JSON.stringify(settingsData) 
});

export const changePassword = (passwordData: { 
  current_password: string; 
  new_password: string; 
  confirm_password: string;
}) => apiFetch('/users/me/change-password', { 
  method: 'POST', 
  body: JSON.stringify(passwordData) 
});

// Admin user management endpoints
export const getUsers = (params?: {
  email?: string;
  phone_number?: string;
  status?: string;
  oauth_provider?: string;
  is_email_verified?: boolean;
  is_phone_verified?: boolean;
  two_factor_enabled?: boolean;
  created_after?: string;
  created_before?: string;
  page?: number;
  page_size?: number;
}) => {
  const queryParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });
  }
  return apiFetch(`/users?${queryParams.toString()}`);
};

export const getUserById = (userId: string) => apiFetch(`/users/${userId}`);
export const getUserDetail = (userId: string) => apiFetch(`/users/${userId}/detail`);
export const updateUser = (userId: string, userData: any) => 
  apiFetch(`/users/${userId}`, { method: 'PUT', body: JSON.stringify(userData) });
export const updateUserStatus = (userId: string, status: string) => 
  apiFetch(`/users/${userId}/status`, { method: 'PUT', body: JSON.stringify({ status }) });
export const bulkUserAction = (userIds: string[], action: string) => 
  apiFetch('/users/bulk-action', { method: 'POST', body: JSON.stringify({ user_ids: userIds, action }) });
export const getUserStats = () => apiFetch('/users/stats');
// ========================================================================
// CHAT MANAGEMENT
// ========================================================================

export const getChats = (params?: {
  title?: string;
  language?: string;
  model_preference?: string;
  is_archived?: boolean;
  is_pinned?: boolean;
  created_after?: string;
  created_before?: string;
  updated_after?: string;
  updated_before?: string;
  message_count_min?: number;
  message_count_max?: number;
  page?: number;
  page_size?: number;
}) => {
  const queryParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });
  }
  return apiFetch(`/chat?${queryParams.toString()}`);
};

export const createChat = (chatData: {
  title?: string;
  description?: string;
  context?: string;
  language?: string;
  model_preference?: string;
  max_tokens?: number;
  temperature?: number;
}) => apiFetch('/chat', { method: 'POST', body: JSON.stringify(chatData) });

export const getChat = (chatId: string, include_messages: boolean = true) => 
  apiFetch(`/chat/${chatId}?include_messages=${include_messages}`);

export const updateChat = (chatId: string, chatData: {
  title?: string;
  description?: string;
  context?: string;
  language?: string;
  model_preference?: string;
  max_tokens?: number;
  temperature?: number;
  is_archived?: boolean;
  is_pinned?: boolean;
}) => apiFetch(`/chat/${chatId}`, { method: 'PUT', body: JSON.stringify(chatData) });

export const deleteChat = (chatId: string) => apiFetch(`/chat/${chatId}`, { method: 'DELETE' });

export const sendMessage = (chatId: string, messageData: {
  message: string;
  message_type?: string;
  attachments?: string[];
  context?: string;
  language?: string;
  priority?: string;
}) => apiFetch(`/chat/${chatId}/messages`, { method: 'POST', body: JSON.stringify(messageData) });

export const getChatMessages = (chatId: string, limit: number = 100, offset: number = 0) => 
  apiFetch(`/chat/${chatId}/messages?limit=${limit}&offset=${offset}`);

export const addFeedbackToMessage = (messageId: string, feedbackData: {
  rating: number;
  feedback_type: string;
  comment?: string;
  category?: string;
}) => apiFetch(`/chat/messages/${messageId}/feedback`, { method: 'POST', body: JSON.stringify(feedbackData) });

export const getChatSettings = () => apiFetch('/chat/settings');
export const updateChatSettings = (settingsData: {
  default_language?: string;
  default_model?: string;
  default_max_tokens?: number;
  default_temperature?: number;
  auto_archive_after_days?: number;
  max_chats_per_user?: number;
  max_messages_per_chat?: number;
  enable_voice_input?: boolean;
  enable_file_upload?: boolean;
  enable_image_analysis?: boolean;
  enable_context_memory?: boolean;
  enable_chat_history?: boolean;
  enable_analytics?: boolean;
  enable_feedback?: boolean;
}) => apiFetch('/chat/settings', { method: 'PUT', body: JSON.stringify(settingsData) });

export const getChatAnalytics = (params?: {
  date_range_start?: string;
  date_range_end?: string;
  group_by?: string;
  include_message_content?: boolean;
  include_user_metrics?: boolean;
  include_model_metrics?: boolean;
}) => {
  const queryParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });
  }
  return apiFetch(`/chat/analytics?${queryParams.toString()}`);
};

export const bulkChatAction = (chatIds: string[], action: string) => 
  apiFetch('/chat/bulk-action', { method: 'POST', body: JSON.stringify({ chat_ids: chatIds, action }) });

export const exportChat = (chatId: string, exportData: {
  format?: string;
  include_metadata?: boolean;
  include_context?: boolean;
  include_attachments?: boolean;
  date_range_start?: string;
  date_range_end?: string;
}) => apiFetch(`/chat/${chatId}/export`, { method: 'POST', body: JSON.stringify(exportData) });

export const getChatStats = () => apiFetch('/chat/stats');

// ========================================================================
// SESSION MANAGEMENT
// ========================================================================

export const getSessions = (params?: {
  user_id?: string;
  is_active?: boolean;
  is_mobile?: boolean;
  ip_address?: string;
  created_after?: string;
  created_before?: string;
  expires_after?: string;
  expires_before?: string;
  page?: number;
  page_size?: number;
}) => {
  const queryParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });
  }
  return apiFetch(`/sessions?${queryParams.toString()}`);
};

export const getSessionStats = () => apiFetch('/sessions/stats');
export const getSessionById = (sessionId: string) => apiFetch(`/sessions/${sessionId}`);
export const createSession = (sessionData: {
  device_info?: string;
  ip_address?: string;
  user_agent?: string;
  location?: string;
  is_mobile?: boolean;
  expires_in_hours?: number;
}) => apiFetch('/sessions', { method: 'POST', body: JSON.stringify(sessionData) });
export const deleteSession = (sessionId: string) => apiFetch(`/sessions/${sessionId}`, { method: 'DELETE' });
export const getActiveSessions = () => apiFetch('/sessions/me/active');
export const logoutAllSessions = () => apiFetch('/sessions/me/all', { method: 'DELETE' });
export const logoutSession = (sessionId?: string, logout_all: boolean = false) => 
  apiFetch('/sessions/logout', { method: 'POST', body: JSON.stringify({ session_id: sessionId, logout_all }) });
export const getCurrentSession = () => apiFetch('/sessions/current');
export const cleanupExpiredSessions = () => apiFetch('/sessions/cleanup', { method: 'DELETE' });

// ========================================================================
// INTELLIGENT Q&A
// ========================================================================

export const askIntelligentQuestion = (params: {
  question: string;
  user_id?: string;
  context?: string;
  language?: string;
}) => {
  const queryParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) queryParams.append(key, value.toString());
  });
  return apiFetch(`/intelligent-qa/ask?${queryParams.toString()}`, { method: 'POST' });
};

export const getSimilarQuestions = (question: string, limit: number = 5) => 
  apiFetch(`/intelligent-qa/similar-questions?question=${encodeURIComponent(question)}&limit=${limit}`);

export const augmentQuestionVariants = (question: string, answer: string) => 
  apiFetch(`/intelligent-qa/augment-variants?question=${encodeURIComponent(question)}&answer=${encodeURIComponent(answer)}`, { method: 'POST' });

export const getIntelligentQAHealth = () => apiFetch('/intelligent-qa/health');
export const initializeIntelligentQA = () => apiFetch('/intelligent-qa/initialize', { method: 'POST' });
export const getWebScrapingStatus = () => apiFetch('/intelligent-qa/web-scraping-status');

// ========================================================================
// QUESTIONS & ANSWERS
// ========================================================================

export const createQuestion = (question: string) => 
  apiFetch('/questions', { method: 'POST', body: JSON.stringify({ question }) });

export const getQuestions = () => apiFetch('/questions');
export const getQuestionById = (questionId: string) => apiFetch(`/questions/${questionId}`);
export const deleteQuestion = (questionId: string) => apiFetch(`/questions/${questionId}`, { method: 'DELETE' });

export const createAnswer = (answerData: {
  answer: string;
  question_id: string;
  author: string;
}) => apiFetch('/answers', { method: 'POST', body: JSON.stringify(answerData) });

export const getAnswersByQuestion = (questionId: string) => apiFetch(`/answers/question/${questionId}`);
export const getAnswerById = (answerId: string) => apiFetch(`/answers/${answerId}`);
export const deleteAnswer = (answerId: string) => apiFetch(`/answers/${answerId}`, { method: 'DELETE' });

// ========================================================================
// SMTP CONFIGURATION
// ========================================================================

export const getSMTPProviders = () => apiFetch('/smtp/providers');
export const getSMTPProvider = (provider: string) => apiFetch(`/smtp/providers/${provider}`);
export const testSMTPConnection = (testData: {
  email: string;
  password: string;
  provider?: string;
}) => apiFetch('/smtp/test', { method: 'POST', body: JSON.stringify(testData) });
export const detectSMTPProvider = (email: string) => 
  apiFetch('/smtp/detect-provider', { method: 'POST', body: JSON.stringify({ email }) });
export const getSupportedDomains = () => apiFetch('/smtp/supported-domains');
export const configureSMTP = (configData: {
  email: string;
  password: string;
  provider: string;
  use_ssl?: boolean;
  custom_host?: string;
  custom_port?: number;
}) => apiFetch('/smtp/configure', { method: 'POST', body: JSON.stringify(configData) });
export const getSMTPHealth = () => apiFetch('/smtp/health');

// ========================================================================
// SYSTEM ENDPOINTS
// ========================================================================

export const getSystemHealth = () => apiFetch('/test/health');
export const getSystemInfo = () => apiFetch('/');
export const greetUser = (name: string) => apiFetch(`/hello/${name}`);