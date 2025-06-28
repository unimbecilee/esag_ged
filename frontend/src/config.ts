interface Config {
  API_URL: string;
  APP_NAME: string;
  APP_VERSION: string;
  MAX_FILE_SIZE: number;
  SUPPORTED_FILE_TYPES: string[];
  OCR_LANGUAGES: Array<{
    code: string;
    name: string;
    flag: string;
  }>;
  PAGINATION: {
    DEFAULT_PAGE_SIZE: number;
    MAX_PAGE_SIZE: number;
  };
  FEATURES: {
    DOCUMENT_PREVIEW: boolean;
    DOCUMENT_OCR: boolean;
    DOCUMENT_COMMENTS: boolean;
    DOCUMENT_TAGS: boolean;
    DOCUMENT_VERSIONS: boolean;
    DOCUMENT_CHECKOUT: boolean;
    DOCUMENT_SUBSCRIPTION: boolean;
    BATCH_OPERATIONS: boolean;
    ADVANCED_SEARCH: boolean;
    ANALYTICS: boolean;
  };
}

const config: Config = {
  API_URL: process.env.REACT_APP_API_URL || 'https://web-production-ae27.up.railway.app',
  APP_NAME: 'ESAG GED',
  APP_VERSION: '2.0.0',
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  SUPPORTED_FILE_TYPES: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'application/zip',
    'application/x-rar-compressed'
  ],
  OCR_LANGUAGES: [
    { code: 'fra', name: 'Français', flag: '🇫🇷' },
    { code: 'eng', name: 'English', flag: '🇺🇸' },
    { code: 'spa', name: 'Español', flag: '🇪🇸' },
    { code: 'deu', name: 'Deutsch', flag: '🇩🇪' },
    { code: 'ita', name: 'Italiano', flag: '🇮🇹' },
    { code: 'por', name: 'Português', flag: '🇵🇹' },
    { code: 'rus', name: 'Русский', flag: '🇷🇺' },
    { code: 'ara', name: 'العربية', flag: '🇸🇦' },
    { code: 'chi_sim', name: '中文 (简体)', flag: '🇨🇳' },
    { code: 'jpn', name: '日本語', flag: '🇯🇵' }
  ],
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100
  },
  FEATURES: {
    DOCUMENT_PREVIEW: true,
    DOCUMENT_OCR: true,
    DOCUMENT_COMMENTS: true,
    DOCUMENT_TAGS: true,
    DOCUMENT_VERSIONS: true,
    DOCUMENT_CHECKOUT: true,
    DOCUMENT_SUBSCRIPTION: true,
    BATCH_OPERATIONS: true,
    ADVANCED_SEARCH: true,
    ANALYTICS: true
  }
};

export default config;
export const { API_URL } = config; 