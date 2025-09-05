// // src/services/api.ts
// import { jwtDecode } from 'jwt-decode';

// const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

// // دالة مساعدة لمعالجة استجابات API بشكل موحد (لا تغيير هنا)
// const handleResponse = async (response: Response) => {
//   if (response.status === 204) {
//     return;
//   }
//   const data = await response.json();
//   if (!response.ok) {
//     const errorMessage = data.message || data.detail || 'An unknown error occurred.';
//     throw new Error(errorMessage);
//   }
//   return data;
// };

// // دالة لتجديد التوكن (تم تصحيح المسار)
// const refreshToken = async () => {
//   const refreshToken = localStorage.getItem('refreshToken');
//   if (!refreshToken) throw new Error("No refresh token available");

//   const response = await fetch(`${API_BASE_URL}/api/sessions/refresh/`, { // <-- تم التصحيح
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ refresh_token: refreshToken }),
//   });

//   const data = await handleResponse(response);
//   localStorage.setItem('accessToken', data.access_token);
//   if (data.refresh_token) {
//     localStorage.setItem('refreshToken', data.refresh_token);
//   }
//   return data.access_token;
// };

// // دالة للتحقق من صلاحية التوكن وتجديده إذا لزم الأمر (لا تغيير هنا)
// const getValidAccessToken = async () => {
//   if (typeof window === 'undefined') return null;
  
//   let token = localStorage.getItem('accessToken');
//   if (!token) return null;

//   try {
//     const decoded: { exp: number } = jwtDecode(token);
//     const isExpired = Date.now() >= decoded.exp * 1000 - 60000; 

//     if (isExpired) {
//       console.log("Access token expired or expiring soon, refreshing...");
//       token = await refreshToken();
//     }
//     return token;
//   } catch (error) {
//     console.error("Invalid token, attempting refresh:", error);
//     try {
//       token = await refreshToken();
//       return token;
//     } catch (refreshError) {
//       console.error("Failed to refresh token:", refreshError);
//       localStorage.removeItem('accessToken');
//       localStorage.removeItem('refreshToken');
//       return null;
//     }
//   }
// };

// // Interceptor: دالة fetch مخصصة (تم تعديلها لتضيف /api/ تلقائياً)
// const apiFetch = async (url: string, options: RequestInit = {}) => {
//   const token = await getValidAccessToken();
  
//   const headers: HeadersInit = {
//     'Content-Type': 'application/json',
//     ...options.headers,
//   };

//   if (token) {
//     headers['Authorization'] = `Bearer ${token}`;
//   }

//   // --- تعديل حاسم: إضافة /api/ تلقائياً لجميع الطلبات ---
//   const fullUrl = `${API_BASE_URL}/api${url}`;
//   const response = await fetch(fullUrl, { ...options, headers });
//   return handleResponse(response);
// };

// // ========================================================================
// // AUTHENTICATION ENDPOINTS
// // ========================================================================

// // تستخدم fetch مباشرة لأنها لا تحتاج إلى توكن مصادقة
// export const loginUser = async (email, password) => {
//   const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ email, password }),
//   });
//   // handleResponse سيقوم بمعالجة الخطأ أو إرجاع البيانات
//   return handleResponse(response); 
// };

// // تستخدم fetch مباشرة لأنها لا تحتاج إلى توكن مصادقة
// export const registerUser = async (userData) => {
//   const response = await fetch(`${API_BASE_URL}/api/users/register/`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify(userData),
//   });
//   return handleResponse(response);
// };

// // (ملاحظة: هذه الدوال لم نقم ببناء الواجهة الخلفية لها بعد، ولكن مساراتها صحيحة الآن)
// export const verifyEmail = (uid: string, token: string) => 
//   fetch(`${API_BASE_URL}/api/users/verify-email/${uid}/${token}/`).then(handleResponse);

// export const forgotPassword = (email: string) => 
//   fetch(`${API_BASE_URL}/api/users/forgot-password/`, { method: 'POST', body: JSON.stringify({ email }) }).then(handleResponse);

// export const resetPassword = (token: string, new_password: string, confirm_password: string) => 
//   fetch(`${API_BASE_URL}/api/users/reset-password/`, { method: 'POST', body: JSON.stringify({ token, new_password, confirm_password }) }).then(handleResponse);

// // تم تصحيح المسار ليتطابق مع UserProfileView
// export const getCurrentUser = () => 
//   apiFetch('/users/me/profile/');

// // ========================================================================
// // USER MANAGEMENT & SETTINGS
// // ========================================================================

// export const getUserProfile = () => 
//   apiFetch('/users/me/profile/');

// export const updateUserProfile = (profileData: { first_name?; last_name?; phone_number?; profile_picture?}) => 
//   apiFetch('/users/me/profile/', { method: 'PUT', body: JSON.stringify(profileData) });

// export const changePassword = (passwordData: { current_password; new_password; confirm_password }) => 
//   apiFetch('/users/me/change-password/', { method: 'POST', body: JSON.stringify(passwordData) });

// export const deleteAccount = () => 
//   apiFetch('/users/me/profile/', { method: 'DELETE' });

// export const getUserSettings = () => 
//   apiFetch('/users/me/settings/');

// export const updateUserSettings = (settingsData) => 
//   apiFetch('/users/me/settings/', { method: 'PUT', body: JSON.stringify(settingsData) });

// // ========================================================================
// // CHAT
// // ========================================================================

// export const getChats = async () => {
//   const data = await apiFetch('/chat/');
//   return data; // الواجهة الخلفية ترجع قائمة مباشرة
// };

// export const createChat = (chatData: { title?: string }) => 
//   apiFetch('/chat/', { method: 'POST', body: JSON.stringify(chatData) });

// export const sendMessage = (chatId: string, messageData: { message: string }) => 
//   apiFetch(`/chat/${chatId}/messages/`, { method: 'POST', body: JSON.stringify(messageData) });

// export const getChatMessages = (chatId: string) => 
//   apiFetch(`/chat/${chatId}/messages/`);

// export const addFeedbackToMessage = (messageId: string, feedbackData: { rating: number; feedback_type: string; comment?: string }) => {
//   return apiFetch(`/chat/messages/${messageId}/feedback/`, {
//     method: 'POST',
//     body: JSON.stringify(feedbackData),
//   });
// };

// // (ملاحظة: هذه الدوال لم نقم ببناء الواجهة الخلفية لها بعد، ولكن مساراتها صحيحة الآن)
// export const clearChatHistory = () => 
//   apiFetch('/chat/clear-history/', { method: 'POST' });

// export const exportUserData = () => 
//   apiFetch('/users/me/export/', { method: 'POST' });



// src/services/api.ts (الكود الكامل والمُصحح)
import { jwtDecode } from 'jwt-decode';

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

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

  const response = await fetch(`${API_BASE_URL}/api/sessions/refresh/`, {
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
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const fullUrl = `${API_BASE_URL}/api${url}`;
  const response = await fetch(fullUrl, { ...options, headers });
  return handleResponse(response);
};

// ========================================================================
// AUTHENTICATION
// ========================================================================

export const loginUser = async (email, password) => {
  const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  // --- تعديل مهم: loginUser الآن فقط ترجع البيانات ---
  // لا تقوم بحفظ أي شيء في localStorage
  return handleResponse(response);
};

export const registerUser = async (userData) => {
  const response = await fetch(`${API_BASE_URL}/api/users/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });
  return handleResponse(response);
};

export const getCurrentUser = () => apiFetch('/users/me/profile/');

// ========================================================================
// USER MANAGEMENT
// ========================================================================

export const getUserProfile = () => apiFetch('/users/me/profile/');
export const updateUserProfile = (profileData) => apiFetch('/users/me/profile/', { method: 'PUT', body: JSON.stringify(profileData) });
export const getUserSettings = () => apiFetch('/users/me/settings/');
export const updateUserSettings = (settingsData) => apiFetch('/users/me/settings/', { method: 'PUT', body: JSON.stringify(settingsData) });
export const changePassword = (passwordData) => 
  apiFetch('/users/me/change-password/', { method: 'POST', body: JSON.stringify(passwordData) });

export const deleteAccount = () => 
  apiFetch('/users/me/delete/', { method: 'DELETE' });
// ========================================================================
// CHAT
// ========================================================================

export const getChats = () => apiFetch('/chat/');
export const createChat = (chatData) => apiFetch('/chat/', { method: 'POST', body: JSON.stringify(chatData) });
export const sendMessage = (chatId, messageData) => apiFetch(`/chat/${chatId}/messages/`, { method: 'POST', body: JSON.stringify(messageData) });
export const getChatMessages = (chatId) => apiFetch(`/chat/${chatId}/messages/`);
export const addFeedbackToMessage = (messageId, feedbackData) => apiFetch(`/chat/messages/${messageId}/feedback/`, { method: 'POST', body: JSON.stringify(feedbackData) });
export const clearChatHistory = () => 
  apiFetch('/chat/clear-history/', { method: 'POST' });

export const exportUserData = () => 
  apiFetch('/users/me/export/', { method: 'POST' });