-- PostgreSQL Security Initialization Script for ITDO ERP System v2
-- This script sets up security-related database configurations

-- Create monitoring user for health checks
CREATE USER monitoring WITH ENCRYPTED PASSWORD 'monitoring_secure_password_change_me';
GRANT CONNECT ON DATABASE itdo_erp_db TO monitoring;
GRANT USAGE ON SCHEMA public TO monitoring;
GRANT SELECT ON pg_stat_database TO monitoring;
GRANT SELECT ON pg_stat_activity TO monitoring;

-- Create backup user
CREATE USER backup_user WITH ENCRYPTED PASSWORD 'backup_secure_password_change_me';
GRANT CONNECT ON DATABASE itdo_erp_db TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;

-- Create read-only user for reporting
CREATE USER readonly_user WITH ENCRYPTED PASSWORD 'readonly_secure_password_change_me';
GRANT CONNECT ON DATABASE itdo_erp_db TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;

-- Enable row level security on sensitive tables (will be configured per table)
-- This is a placeholder - actual RLS policies should be defined in your application

-- Create audit log table for security events
CREATE TABLE IF NOT EXISTS security_audit_log (
    id SERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,
    user_id UUID,
    username VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    resource_accessed TEXT,
    action_performed VARCHAR(100),
    success BOOLEAN,
    error_message TEXT,
    session_id VARCHAR(255),
    additional_data JSONB
);

-- Create index for efficient querying
CREATE INDEX idx_security_audit_log_timestamp ON security_audit_log(event_timestamp);
CREATE INDEX idx_security_audit_log_user_id ON security_audit_log(user_id);
CREATE INDEX idx_security_audit_log_event_type ON security_audit_log(event_type);
CREATE INDEX idx_security_audit_log_ip_address ON security_audit_log(ip_address);

-- Grant permissions on audit table
GRANT INSERT ON security_audit_log TO itdo_user;
GRANT SELECT ON security_audit_log TO readonly_user;
GRANT USAGE ON SEQUENCE security_audit_log_id_seq TO itdo_user;

-- Create function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    p_event_type VARCHAR(50),
    p_user_id UUID DEFAULT NULL,
    p_username VARCHAR(255) DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_resource_accessed TEXT DEFAULT NULL,
    p_action_performed VARCHAR(100) DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL,
    p_session_id VARCHAR(255) DEFAULT NULL,
    p_additional_data JSONB DEFAULT NULL
) RETURNS void AS $$
BEGIN
    INSERT INTO security_audit_log (
        event_type, user_id, username, ip_address, user_agent,
        resource_accessed, action_performed, success, error_message,
        session_id, additional_data
    ) VALUES (
        p_event_type, p_user_id, p_username, p_ip_address, p_user_agent,
        p_resource_accessed, p_action_performed, p_success, p_error_message,
        p_session_id, p_additional_data
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION log_security_event TO itdo_user;

-- Create table for tracking failed login attempts
CREATE TABLE IF NOT EXISTS failed_login_attempts (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    username VARCHAR(255),
    attempt_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    additional_info JSONB
);

-- Create index for efficient querying
CREATE INDEX idx_failed_login_attempts_ip ON failed_login_attempts(ip_address);
CREATE INDEX idx_failed_login_attempts_timestamp ON failed_login_attempts(attempt_timestamp);
CREATE INDEX idx_failed_login_attempts_username ON failed_login_attempts(username);

-- Grant permissions
GRANT INSERT, SELECT ON failed_login_attempts TO itdo_user;
GRANT USAGE ON SEQUENCE failed_login_attempts_id_seq TO itdo_user;

-- Create function to check if IP should be blocked
CREATE OR REPLACE FUNCTION is_ip_blocked(
    p_ip_address INET,
    p_max_attempts INTEGER DEFAULT 5,
    p_time_window_minutes INTEGER DEFAULT 15
) RETURNS BOOLEAN AS $$
DECLARE
    attempt_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO attempt_count
    FROM failed_login_attempts
    WHERE ip_address = p_ip_address
      AND attempt_timestamp > (CURRENT_TIMESTAMP - INTERVAL '1 minute' * p_time_window_minutes);
    
    RETURN attempt_count >= p_max_attempts;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION is_ip_blocked TO itdo_user;

-- Create function to clean old audit logs (for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(
    p_retention_days INTEGER DEFAULT 365
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM security_audit_log
    WHERE event_timestamp < (CURRENT_TIMESTAMP - INTERVAL '1 day' * p_retention_days);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM failed_login_attempts
    WHERE attempt_timestamp < (CURRENT_TIMESTAMP - INTERVAL '1 day' * p_retention_days);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create extension for better password hashing if not exists
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for pg_stat_statements if not exists (for query monitoring)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Set up automatic cleanup job (requires pg_cron extension in production)
-- This would need to be set up separately in production:
-- SELECT cron.schedule('cleanup-audit-logs', '0 2 * * *', 'SELECT cleanup_old_audit_logs(365);');

-- Security settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
ALTER SYSTEM SET log_checkpoints = 'on';
ALTER SYSTEM SET log_lock_waits = 'on';

-- Ensure proper permissions on main user
ALTER USER itdo_user SET search_path TO public;

-- Create schema for sensitive data if needed
-- CREATE SCHEMA IF NOT EXISTS sensitive AUTHORIZATION itdo_user;

-- Log successful initialization
SELECT log_security_event(
    'database_initialization',
    NULL,
    'system',
    '127.0.0.1',
    'PostgreSQL Init Script',
    'database',
    'security_setup',
    TRUE,
    NULL,
    NULL,
    '{"script_version": "1.0", "timestamp": "' || CURRENT_TIMESTAMP || '"}'::jsonb
);

COMMIT;