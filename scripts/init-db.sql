-- Database initialization script for AI Code Review Multi-Agent System
-- This script sets up the initial database schema and data

-- Create database if it doesn't exist (PostgreSQL specific)
-- For Docker, this is handled by POSTGRES_DB environment variable

-- ============================================================================
-- EXTENSION SETUP
-- ============================================================================

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for full-text search capabilities
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- SCHEMA CREATION
-- ============================================================================

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS ai_agents;
CREATE SCHEMA IF NOT EXISTS memory_system;
CREATE SCHEMA IF NOT EXISTS analysis_results;
CREATE SCHEMA IF NOT EXISTS audit_logs;

-- ============================================================================
-- AI AGENTS TABLES
-- ============================================================================

-- Agent configurations and metadata
CREATE TABLE IF NOT EXISTS ai_agents.agent_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(100) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(agent_type, agent_name)
);

-- Agent sessions for tracking interactions
CREATE TABLE IF NOT EXISTS ai_agents.agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES ai_agents.agent_configs(id),
    session_token VARCHAR(255) UNIQUE,
    agdk_session_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_agent_sessions_token (session_token),
    INDEX idx_agent_sessions_agdk (agdk_session_id)
);

-- ============================================================================
-- MEMORY SYSTEM TABLES
-- ============================================================================

-- Memory patterns for learning
CREATE TABLE IF NOT EXISTS memory_system.patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(100) NOT NULL,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence_score DECIMAL(5,3) DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    is_validated BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_patterns_type (pattern_type),
    INDEX idx_patterns_confidence (confidence_score),
    INDEX idx_patterns_usage (usage_count)
);

-- Learning feedback for pattern validation
CREATE TABLE IF NOT EXISTS memory_system.learning_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID REFERENCES memory_system.patterns(id),
    feedback_type VARCHAR(50) NOT NULL,
    feedback_value DECIMAL(5,3) NOT NULL,
    source VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_feedback_pattern (pattern_id),
    INDEX idx_feedback_type (feedback_type)
);

-- Memory cache for fast retrieval
CREATE TABLE IF NOT EXISTS memory_system.memory_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_data JSONB NOT NULL,
    expiry_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_cache_expiry (expiry_time)
);

-- ============================================================================
-- ANALYSIS RESULTS TABLES
-- ============================================================================

-- Code analysis sessions
CREATE TABLE IF NOT EXISTS analysis_results.analysis_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255),
    repository_url VARCHAR(500),
    commit_hash VARCHAR(40),
    branch_name VARCHAR(255),
    analysis_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    configuration JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_analysis_sessions_status (status),
    INDEX idx_analysis_sessions_type (analysis_type)
);

-- Analysis findings
CREATE TABLE IF NOT EXISTS analysis_results.findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES analysis_results.analysis_sessions(id),
    finding_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(5,3) DEFAULT 0.0,
    file_path VARCHAR(1000),
    line_number INTEGER,
    column_number INTEGER,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    recommendation TEXT,
    evidence JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_findings_session (session_id),
    INDEX idx_findings_type (finding_type),
    INDEX idx_findings_severity (severity),
    INDEX idx_findings_confidence (confidence_score),
    INDEX idx_findings_file (file_path)
);

-- Analysis metrics
CREATE TABLE IF NOT EXISTS analysis_results.metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES analysis_results.analysis_sessions(id),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(10,3),
    metric_unit VARCHAR(50),
    metric_category VARCHAR(100),
    metadata JSONB,
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_metrics_session (session_id),
    INDEX idx_metrics_name (metric_name),
    INDEX idx_metrics_category (metric_category)
);

-- ============================================================================
-- AUDIT LOGS TABLES
-- ============================================================================

-- System audit logs
CREATE TABLE IF NOT EXISTS audit_logs.system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    event_data JSONB,
    severity VARCHAR(20) DEFAULT 'info',
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_system_events_type (event_type),
    INDEX idx_system_events_source (event_source),
    INDEX idx_system_events_severity (severity),
    INDEX idx_system_events_created (created_at)
);

-- API access logs
CREATE TABLE IF NOT EXISTS audit_logs.api_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(255),
    method VARCHAR(10) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    status_code INTEGER,
    response_time INTEGER, -- in milliseconds
    request_size INTEGER,
    response_size INTEGER,
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_api_access_endpoint (endpoint),
    INDEX idx_api_access_status (status_code),
    INDEX idx_api_access_created (created_at)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_findings_description_fts 
ON analysis_results.findings USING gin(to_tsvector('english', description));

CREATE INDEX IF NOT EXISTS idx_findings_recommendation_fts 
ON analysis_results.findings USING gin(to_tsvector('english', recommendation));

-- JSON indexes for better JSONB performance
CREATE INDEX IF NOT EXISTS idx_agent_configs_configuration 
ON ai_agents.agent_configs USING gin(configuration);

CREATE INDEX IF NOT EXISTS idx_patterns_pattern_data 
ON memory_system.patterns USING gin(pattern_data);

CREATE INDEX IF NOT EXISTS idx_findings_evidence 
ON analysis_results.findings USING gin(evidence);

CREATE INDEX IF NOT EXISTS idx_findings_metadata 
ON analysis_results.findings USING gin(metadata);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active agent sessions view
CREATE OR REPLACE VIEW ai_agents.active_sessions AS
SELECT 
    s.id,
    s.session_token,
    s.agdk_session_id,
    c.agent_type,
    c.agent_name,
    s.started_at,
    s.metadata
FROM ai_agents.agent_sessions s
JOIN ai_agents.agent_configs c ON s.agent_id = c.id
WHERE s.status = 'active' AND s.ended_at IS NULL;

-- Recent findings view
CREATE OR REPLACE VIEW analysis_results.recent_findings AS
SELECT 
    f.id,
    f.finding_type,
    f.severity,
    f.confidence_score,
    f.file_path,
    f.title,
    f.description,
    s.session_name,
    s.repository_url,
    f.created_at
FROM analysis_results.findings f
JOIN analysis_results.analysis_sessions s ON f.session_id = s.id
WHERE f.created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY f.created_at DESC;

-- High-confidence patterns view
CREATE OR REPLACE VIEW memory_system.validated_patterns AS
SELECT 
    id,
    pattern_type,
    pattern_name,
    confidence_score,
    usage_count,
    created_at,
    updated_at
FROM memory_system.patterns
WHERE confidence_score >= 0.8 AND is_validated = true
ORDER BY confidence_score DESC, usage_count DESC;

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updating timestamps
CREATE TRIGGER update_agent_configs_updated_at 
    BEFORE UPDATE ON ai_agents.agent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patterns_updated_at 
    BEFORE UPDATE ON memory_system.patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM memory_system.memory_cache 
    WHERE expiry_time IS NOT NULL AND expiry_time < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default agent configurations
INSERT INTO ai_agents.agent_configs (agent_type, agent_name, configuration) VALUES
    ('base_agent', 'primary', '{"agdk_enabled": true, "model": "gemini-1.5-pro"}'),
    ('code_analyzer', 'security', '{"focus": "security", "severity_threshold": 0.7}'),
    ('code_analyzer', 'performance', '{"focus": "performance", "optimization_level": "high"}'),
    ('microservices', 'architecture', '{"pattern_detection": true, "compliance_check": true}')
ON CONFLICT (agent_type, agent_name) DO NOTHING;

-- Insert initial pattern templates
INSERT INTO memory_system.patterns (pattern_type, pattern_name, pattern_data, confidence_score, is_validated) VALUES
    ('security', 'sql_injection_detection', '{"keywords": ["query", "execute", "sql"], "risk_indicators": ["user_input", "concatenation"]}', 0.9, true),
    ('performance', 'n_plus_one_query', '{"pattern": "loop_with_query", "indicators": ["for", "while", "each", "select"]}', 0.85, true),
    ('maintainability', 'long_method', '{"metrics": {"lines": 50, "complexity": 10}, "threshold": "high"}', 0.8, true)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- CLEANUP AND MAINTENANCE
-- ============================================================================

-- Create a maintenance function to be run periodically
CREATE OR REPLACE FUNCTION perform_maintenance()
RETURNS TEXT AS $$
DECLARE
    cache_cleaned INTEGER;
    result_text TEXT;
BEGIN
    -- Clean expired cache
    cache_cleaned := clean_expired_cache();
    
    -- Update statistics
    ANALYZE;
    
    result_text := FORMAT('Maintenance completed: %s cache entries cleaned', cache_cleaned);
    
    -- Log maintenance
    INSERT INTO audit_logs.system_events (event_type, event_source, event_data) 
    VALUES ('maintenance', 'database', json_build_object('cache_cleaned', cache_cleaned));
    
    RETURN result_text;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANTS AND PERMISSIONS
-- ============================================================================

-- Create application user (if needed)
-- CREATE USER ai_app_user WITH PASSWORD 'secure_password';

-- Grant permissions
-- GRANT USAGE ON SCHEMA ai_agents, memory_system, analysis_results, audit_logs TO ai_app_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai_agents, memory_system, analysis_results, audit_logs TO ai_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai_agents, memory_system, analysis_results, audit_logs TO ai_app_user;