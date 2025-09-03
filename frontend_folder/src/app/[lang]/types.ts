// src/app/types.ts

// Basic Message Interface
export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isTyping?: boolean;
  attachments?: FileAttachment[];
  feedback?: MessageFeedback;
}

// File Attachment Interface
export interface FileAttachment {
  id: string;
  name: string;
  size: number;
  type: string;
  file?: File;
  url?: string;
  uploaded_at?: Date;
}

// Message Feedback Interface
export interface MessageFeedback {
  id: string;
  rating: number;
  feedback_type: string;
  comment?: string;
  created_at: Date;
}

// Chat Interface
export interface Chat {
  id: string;
  title: string;
  description?: string;
  context?: string;
  language?: string;
  created_at: Date;
  updated_at: Date;
  last_message_at?: Date;
  message_count: number;
  is_archived: boolean;
}

// User Interface
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string;
  profile_picture?: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
  last_login?: Date;
  subscription_tier?: string;
  settings?: UserSettings;
}

// User Settings Interface
export interface UserSettings {
  language: string;
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    email: boolean;
    push: boolean;
    chat: boolean;
  };
  privacy: {
    profile_visibility: 'public' | 'private' | 'friends';
    show_online_status: boolean;
  };
}

// Question Interface
export interface Question {
  id: string;
  title: string;
  content: string;
  category?: string;
  tags: string[];
  author_id: string;
  author_name: string;
  created_at: Date;
  updated_at: Date;
  view_count: number;
  answer_count: number;
  is_answered: boolean;
  is_featured: boolean;
}

// Answer Interface
export interface Answer {
  id: string;
  content: string;
  question_id: string;
  author_id: string;
  author_name: string;
  is_ai_generated: boolean;
  is_accepted: boolean;
  created_at: Date;
  updated_at: Date;
  upvotes: number;
  downvotes: number;
}

// Session Interface
export interface Session {
  id: string;
  user_id: string;
  created_at: Date;
  expires_at: Date;
  is_active: boolean;
  ip_address?: string;
  user_agent?: string;
  last_activity: Date;
}

// API Response Interfaces
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
  timestamp: Date;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Error Interface
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
  timestamp: Date;
}

// File Upload Response
export interface FileUploadResponse {
  id: string;
  filename: string;
  original_name: string;
  size: number;
  type: string;
  url: string;
  uploaded_at: Date;
}

// SMTP Provider Interface
export interface SmtpProvider {
  id: string;
  name: string;
  host: string;
  port: number;
  username: string;
  use_tls: boolean;
  is_active: boolean;
  created_at: Date;
}

// OAuth Provider Interface
export interface OAuthProvider {
  id: string;
  name: string;
  client_id: string;
  redirect_uri: string;
  scopes: string[];
  is_active: boolean;
}

// System Information Interface
export interface SystemInfo {
  version: string;
  uptime: number;
  memory_usage: {
    total: number;
    used: number;
    free: number;
  };
  cpu_usage: number;
  disk_usage: {
    total: number;
    used: number;
    free: number;
  };
  active_users: number;
  total_requests: number;
}

// Form Validation Interfaces
export interface ValidationError {
  field: string;
  message: string;
}

export interface FormState<T> {
  data: T;
  errors: { [K in keyof T]?: string };
  isSubmitting: boolean;
  isValid: boolean;
}

// Chat Message API Response
export interface ChatMessageResponse {
  id: string;
  message: string;
  is_ai_response: boolean;
  created_at: string;
  updated_at: string;
  chat_id: string;
  user_id?: string;
  attachments?: any[];
}

// Chat API Response
export interface ChatResponse {
  id: string;
  title: string;
  description?: string;
  context?: string;
  language?: string;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  message_count: number;
  is_archived: boolean;
}

// User Profile API Response
export interface UserProfileResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  profile_picture?: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  subscription_tier?: string;
}