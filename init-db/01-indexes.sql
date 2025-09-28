-- Database initialization script for Orchesity IDE OSS
-- This script is run when the PostgreSQL container starts

-- Create additional indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orchestration_requests_session_id ON orchestration_requests(session_id);
CREATE INDEX IF NOT EXISTS idx_orchestration_requests_created_at ON orchestration_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_orchestration_requests_status ON orchestration_requests(status);

CREATE INDEX IF NOT EXISTS idx_orchestration_results_request_id ON orchestration_results(request_id);
CREATE INDEX IF NOT EXISTS idx_orchestration_results_provider ON orchestration_results(provider);

CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

CREATE INDEX IF NOT EXISTS idx_workflows_session_id ON workflows(session_id);
CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);

CREATE INDEX IF NOT EXISTS idx_cache_entries_cache_type ON cache_entries(cache_type);
CREATE INDEX IF NOT EXISTS idx_cache_entries_expires_at ON cache_entries(expires_at);

CREATE INDEX IF NOT EXISTS idx_provider_metrics_provider ON provider_metrics(provider);
CREATE INDEX IF NOT EXISTS idx_provider_metrics_last_updated ON provider_metrics(last_updated);