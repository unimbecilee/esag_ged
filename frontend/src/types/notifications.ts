export interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
  document_id?: number;
  document_title?: string;
  workflow_id?: number;
  priority: number;
  metadata?: any;
  created_by_id?: number;
  expires_at?: string;
}

export interface NotificationStats {
  general: {
    total: number;
    unread: number;
    last_week: number;
    last_month: number;
  };
  by_type: Array<{
    type: string;
    count: number;
  }>;
  activity: Array<{
    date: string;
    count: number;
  }>;
}

export interface NotificationPreferences {
  email_notifications: boolean;
  app_notifications: boolean;
  document_notifications: boolean;
  workflow_notifications: boolean;
  comment_notifications: boolean;
  share_notifications: boolean;
  mention_notifications: boolean;
  digest_frequency: string;
  weekend_notifications: boolean;
}

export interface Subscription {
  id: number;
  document_id: number;
  document_title: string;
  notification_types: string[];
  created_at: string;
  is_active: boolean;
} 
