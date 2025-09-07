// src/utils/logger.ts
import fs from 'fs';
import path from 'path';

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
  stack?: string;
  userId?: string;
  sessionId?: string;
  url?: string;
  userAgent?: string;
}

class FrontendLogger {
  private logLevel: LogLevel;
  private logsDir: string;
  private maxFileSize: number = 10 * 1024 * 1024; // 10MB
  private maxFiles: number = 5;

  constructor() {
    this.logLevel = this.getLogLevelFromEnv();
    this.logsDir = this.getLogsDirectory();
    this.ensureLogsDirectory();
  }

  private getLogLevelFromEnv(): LogLevel {
    const level = process.env.NEXT_PUBLIC_LOG_LEVEL || 'INFO';
    switch (level.toUpperCase()) {
      case 'DEBUG': return LogLevel.DEBUG;
      case 'INFO': return LogLevel.INFO;
      case 'WARN': return LogLevel.WARN;
      case 'ERROR': return LogLevel.ERROR;
      case 'FATAL': return LogLevel.FATAL;
      default: return LogLevel.INFO;
    }
  }

  private getLogsDirectory(): string {
    // In browser, we'll use localStorage for logging
    // In Node.js (SSR), we'll use the logs folder
    if (typeof window === 'undefined') {
      return path.join(process.cwd(), '..', 'logs');
    }
    return 'browser';
  }

  private ensureLogsDirectory(): void {
    if (typeof window !== 'undefined') return;
    
    try {
      if (!fs.existsSync(this.logsDir)) {
        fs.mkdirSync(this.logsDir, { recursive: true });
      }
    } catch (error) {
      console.error('Failed to create logs directory:', error);
    }
  }

  private getLogFileName(level: LogLevel): string {
    const levelName = LogLevel[level].toLowerCase();
    const date = new Date().toISOString().split('T')[0];
    return `frontend_${levelName}_${date}.log`;
  }

  private async writeToFile(entry: LogEntry): Promise<void> {
    if (typeof window !== 'undefined') return;

    try {
      const fileName = this.getLogFileName(entry.level);
      const filePath = path.join(this.logsDir, fileName);
      const logLine = JSON.stringify(entry) + '\n';

      // Check if file exists and rotate if needed
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        if (stats.size > this.maxFileSize) {
          this.rotateLogFile(filePath);
        }
      }

      fs.appendFileSync(filePath, logLine);
    } catch (error) {
      console.error('Failed to write to log file:', error);
    }
  }

  private rotateLogFile(filePath: string): void {
    try {
      const dir = path.dirname(filePath);
      const ext = path.extname(filePath);
      const base = path.basename(filePath, ext);
      
      // Remove oldest log file if we have too many
      for (let i = this.maxFiles - 1; i >= 0; i--) {
        const oldFile = path.join(dir, `${base}.${i}${ext}`);
        if (i === this.maxFiles - 1 && fs.existsSync(oldFile)) {
          fs.unlinkSync(oldFile);
        } else if (i > 0 && fs.existsSync(oldFile)) {
          const newFile = path.join(dir, `${base}.${i + 1}${ext}`);
          fs.renameSync(oldFile, newFile);
        }
      }

      // Rename current file to .1
      const newFile = path.join(dir, `${base}.1${ext}`);
      fs.renameSync(filePath, newFile);
    } catch (error) {
      console.error('Failed to rotate log file:', error);
    }
  }

  private formatLogEntry(level: LogLevel, category: string, message: string, data?: any): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data,
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      userAgent: typeof window !== 'undefined' ? navigator.userAgent : undefined,
    };

    // Add user context if available
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('user');
      if (user) {
        try {
          const userData = JSON.parse(user);
          entry.userId = userData.id;
        } catch (e) {
          // Ignore parsing errors
        }
      }

      // Generate session ID if not exists
      let sessionId = localStorage.getItem('sessionId');
      if (!sessionId) {
        sessionId = `session_${Math.floor(Math.random() * 1000000)}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('sessionId', sessionId);
      }
      entry.sessionId = sessionId;
    }

    // Add stack trace for errors
    if (level >= LogLevel.ERROR) {
      entry.stack = new Error().stack;
    }

    return entry;
  }

  private async log(level: LogLevel, category: string, message: string, data?: any): Promise<void> {
    if (level < this.logLevel) return;

    const entry = this.formatLogEntry(level, category, message, data);
    
    // Console logging
    const levelName = LogLevel[level];
    const timestamp = new Date().toLocaleTimeString();
    const consoleMessage = `[${timestamp}] [${levelName}] [${category}] ${message}`;
    
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(consoleMessage, data || '');
        break;
      case LogLevel.INFO:
        console.info(consoleMessage, data || '');
        break;
      case LogLevel.WARN:
        console.warn(consoleMessage, data || '');
        break;
      case LogLevel.ERROR:
        console.error(consoleMessage, data || '');
        break;
      case LogLevel.FATAL:
        console.error(consoleMessage, data || '');
        break;
    }

    // File logging
    await this.writeToFile(entry);

    // Browser logging (localStorage)
    if (typeof window !== 'undefined') {
      this.logToBrowser(entry);
    }
  }

  private logToBrowser(entry: LogEntry): void {
    try {
      const logs = JSON.parse(localStorage.getItem('frontend_logs') || '[]');
      logs.push(entry);
      
      // Keep only last 1000 logs
      if (logs.length > 1000) {
        logs.splice(0, logs.length - 1000);
      }
      
      localStorage.setItem('frontend_logs', JSON.stringify(logs));
    } catch (error) {
      console.error('Failed to log to browser storage:', error);
    }
  }

  // Public logging methods
  async debug(category: string, message: string, data?: any): Promise<void> {
    await this.log(LogLevel.DEBUG, category, message, data);
  }

  async info(category: string, message: string, data?: any): Promise<void> {
    await this.log(LogLevel.INFO, category, message, data);
  }

  async warn(category: string, message: string, data?: any): Promise<void> {
    await this.log(LogLevel.WARN, category, message, data);
  }

  async error(category: string, message: string, data?: any): Promise<void> {
    await this.log(LogLevel.ERROR, category, message, data);
  }

  async fatal(category: string, message: string, data?: any): Promise<void> {
    await this.log(LogLevel.FATAL, category, message, data);
  }

  // Utility methods
  async logUserAction(action: string, details?: any): Promise<void> {
    await this.info('USER_ACTION', action, details);
  }

  async logApiCall(endpoint: string, method: string, status?: number, duration?: number): Promise<void> {
    await this.info('API_CALL', `${method} ${endpoint}`, { status, duration, endpoint, method });
  }

  async logError(error: Error, context?: string): Promise<void> {
    await this.error('ERROR', error.message, {
      name: error.name,
      stack: error.stack,
      context
    });
  }

  async logPerformance(operation: string, duration: number, details?: any): Promise<void> {
    await this.info('PERFORMANCE', `${operation} took ${duration}ms`, { operation, duration, ...details });
  }

  // Get logs from browser storage
  getBrowserLogs(): LogEntry[] {
    if (typeof window === 'undefined') return [];
    
    try {
      return JSON.parse(localStorage.getItem('frontend_logs') || '[]');
    } catch (error) {
      console.error('Failed to get browser logs:', error);
      return [];
    }
  }

  // Clear browser logs
  clearBrowserLogs(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('frontend_logs');
  }

  // Export logs
  exportLogs(): string {
    const logs = this.getBrowserLogs();
    return JSON.stringify(logs, null, 2);
  }
}

// Create singleton instance
export const logger = new FrontendLogger();

// Convenience functions
export const logDebug = (category: string, message: string, data?: any) => logger.debug(category, message, data);
export const logInfo = (category: string, message: string, data?: any) => logger.info(category, message, data);
export const logWarn = (category: string, message: string, data?: any) => logger.warn(category, message, data);
export const logError = (category: string, message: string, data?: any) => logger.error(category, message, data);
export const logFatal = (category: string, message: string, data?: any) => logger.fatal(category, message, data);

export default logger;
