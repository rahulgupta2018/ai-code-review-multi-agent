"""
Carbon Footprint Analyzer Tool Implementation for ADK Code Review System.

This tool analyzes environmental impact and energy efficiency of code following green software principles.
"""

import time
import re
from typing import Dict, Any, List, Optional

from google.adk.tools.tool_context import ToolContext


def analyze_carbon_footprint(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Analyze carbon footprint and environmental impact of code.
    
    Args:
        tool_context: ADK ToolContext containing session state and parameters
        
    Returns:
        dict: Carbon footprint analysis results with efficiency metrics and green recommendations
    """
    execution_start = time.time()
    
    try:
        # Get code from tool context
        code = tool_context.state.get('code', '')
        language = tool_context.state.get('language', 'python')
        file_path = tool_context.state.get('file_path', 'unknown')
        
        # Check parameters if not in state
        if not code and hasattr(tool_context, 'parameters'):
            code = getattr(tool_context, 'parameters', {}).get('code', '')
            language = getattr(tool_context, 'parameters', {}).get('language', 'python')
            file_path = getattr(tool_context, 'parameters', {}).get('file_path', 'unknown')
        
        if not code:
            return {
                'status': 'error',
                'error_message': 'No code provided for carbon footprint analysis',
                'tool_name': 'analyze_carbon_footprint'
            }
        
        # Perform comprehensive carbon footprint analysis
        carbon_result = {
            'status': 'success',
            'tool_name': 'analyze_carbon_footprint',
            'file_path': file_path,
            'language': language,
            'analysis_type': 'carbon_footprint_analysis',
            'computational_efficiency': {
                'algorithm_complexity': _analyze_algorithm_complexity(code, language),
                'loop_efficiency': _analyze_loop_efficiency(code, language),
                'data_structure_efficiency': _analyze_data_structures(code, language),
                'recursion_analysis': _analyze_recursion_impact(code, language)
            },
            'resource_consumption': {
                'memory_usage_patterns': _analyze_memory_patterns(code, language),
                'cpu_intensive_operations': _analyze_cpu_operations(code, language),
                'io_operations': _analyze_io_operations(code, language),
                'network_efficiency': _analyze_network_operations(code, language)
            },
            'database_efficiency': {
                'query_optimization': _analyze_database_queries(code, language),
                'connection_management': _analyze_db_connections(code, language),
                'data_transfer_optimization': _analyze_data_transfer(code, language)
            },
            'caching_and_optimization': {
                'caching_strategies': _analyze_caching_strategies(code, language),
                'lazy_loading': _analyze_lazy_loading(code, language),
                'data_compression': _analyze_compression_usage(code, language),
                'resource_pooling': _analyze_resource_pooling(code, language)
            },
            'green_software_practices': {
                'energy_efficient_patterns': _identify_energy_patterns(code, language),
                'carbon_aware_practices': _analyze_carbon_practices(code, language),
                'sustainable_architecture': _assess_sustainable_patterns(code, language)
            },
            'environmental_impact_assessment': {},
            'optimization_recommendations': [],
            'green_score': 0,
            'timestamp': time.time()
        }
        
        # Calculate environmental impact
        carbon_result['environmental_impact_assessment'] = _calculate_environmental_impact(carbon_result)
        
        # Generate optimization recommendations
        carbon_result['optimization_recommendations'] = _generate_green_recommendations(carbon_result)
        
        # Calculate overall green score
        carbon_result['green_score'] = _calculate_green_score(carbon_result)
        
        execution_time = time.time() - execution_start
        carbon_result['execution_time_seconds'] = execution_time
        
        # Store results in session state
        current_analysis = tool_context.state.get('carbon_footprint_analysis', {})
        current_analysis[file_path] = carbon_result
        tool_context.state['carbon_footprint_analysis'] = current_analysis
        
        # Update analysis progress
        analysis_progress = tool_context.state.get('analysis_progress', {})
        analysis_progress['carbon_analysis_completed'] = True
        analysis_progress['carbon_analysis_timestamp'] = time.time()
        tool_context.state['analysis_progress'] = analysis_progress
        
        return carbon_result
        
    except Exception as e:
        execution_time = time.time() - execution_start
        error_result = {
            'status': 'error',
            'tool_name': 'analyze_carbon_footprint',
            'error_message': str(e),
            'error_type': type(e).__name__,
            'execution_time_seconds': execution_time
        }
        
        tool_context.state['carbon_footprint_error'] = error_result
        return error_result


def _analyze_algorithm_complexity(code: str, language: str) -> Dict[str, Any]:
    """Analyze algorithmic complexity for energy efficiency."""
    complexity_indicators = {
        'nested_loops': len(re.findall(r'for.*for', code, re.DOTALL)),
        'triple_nested_loops': len(re.findall(r'for.*for.*for', code, re.DOTALL)),
        'while_loops': len(re.findall(r'while\s+', code)),
        'recursive_functions': len(re.findall(r'def\s+(\w+).*\1\s*\(', code)),
        'sorting_operations': len(re.findall(r'\.sort\(|sorted\(', code)),
        'search_operations': len(re.findall(r'\.find\(|\.index\(|in\s+\w+', code))
    }
    
    # Estimate computational complexity impact
    complexity_score = 100
    complexity_score -= complexity_indicators['nested_loops'] * 15
    complexity_score -= complexity_indicators['triple_nested_loops'] * 25
    complexity_score -= complexity_indicators['while_loops'] * 5
    complexity_score -= complexity_indicators['recursive_functions'] * 10
    
    energy_impact = 'low'
    if complexity_score < 50:
        energy_impact = 'high'
    elif complexity_score < 70:
        energy_impact = 'medium'
    
    return {
        'complexity_score': max(0, complexity_score),
        'energy_impact': energy_impact,
        'complexity_indicators': complexity_indicators,
        'estimated_cpu_cycles': _estimate_cpu_cycles(complexity_indicators)
    }


def _analyze_loop_efficiency(code: str, language: str) -> Dict[str, Any]:
    """Analyze loop efficiency for energy consumption."""
    loop_patterns = {
        'list_comprehensions': len(re.findall(r'\[.*for.*in.*\]', code)),
        'generator_expressions': len(re.findall(r'\(.*for.*in.*\)', code)),
        'map_filter_usage': len(re.findall(r'(map|filter|reduce)\s*\(', code)),
        'inefficient_loops': len(re.findall(r'for.*range\(len\(', code)),
        'break_continue_usage': len(re.findall(r'(break|continue)', code)),
        'enumerate_usage': len(re.findall(r'enumerate\s*\(', code))
    }
    
    efficiency_score = 70  # Base score
    efficiency_score += loop_patterns['list_comprehensions'] * 5
    efficiency_score += loop_patterns['generator_expressions'] * 8
    efficiency_score += loop_patterns['map_filter_usage'] * 6
    efficiency_score -= loop_patterns['inefficient_loops'] * 10
    efficiency_score += loop_patterns['enumerate_usage'] * 3
    
    return {
        'efficiency_score': min(100, max(0, efficiency_score)),
        'loop_patterns': loop_patterns,
        'energy_efficient_loops': loop_patterns['list_comprehensions'] + loop_patterns['generator_expressions'],
        'recommendations': _get_loop_recommendations(loop_patterns)
    }


def _analyze_data_structures(code: str, language: str) -> Dict[str, Any]:
    """Analyze data structure efficiency."""
    data_structure_usage = {
        'lists': len(re.findall(r'\[\]|\[.*\]', code)),
        'sets': len(re.findall(r'set\s*\(|{\w+}', code)),
        'dictionaries': len(re.findall(r'dict\s*\(|{.*:.*}', code)),
        'tuples': len(re.findall(r'\(.*,.*\)', code)),
        'deque_usage': len(re.findall(r'deque\s*\(', code)),
        'defaultdict_usage': len(re.findall(r'defaultdict\s*\(', code)),
        'counter_usage': len(re.findall(r'Counter\s*\(', code))
    }
    
    # Score based on efficient data structure usage
    efficiency_score = 60  # Base score
    efficiency_score += data_structure_usage['sets'] * 8  # Sets are efficient for lookups
    efficiency_score += data_structure_usage['dictionaries'] * 6  # Dicts are efficient for key-value
    efficiency_score += data_structure_usage['deque_usage'] * 10  # Deque is efficient for queues
    efficiency_score += data_structure_usage['defaultdict_usage'] * 8
    efficiency_score += data_structure_usage['counter_usage'] * 8
    
    return {
        'efficiency_score': min(100, efficiency_score),
        'data_structure_usage': data_structure_usage,
        'memory_efficiency_rating': _rate_memory_efficiency(data_structure_usage)
    }


def _analyze_recursion_impact(code: str, language: str) -> Dict[str, Any]:
    """Analyze recursion impact on energy consumption."""
    recursion_patterns = {
        'recursive_functions': len(re.findall(r'def\s+(\w+).*\1\s*\(', code)),
        'tail_recursion_optimizable': len(re.findall(r'return\s+\w+\s*\(', code)),
        'memoization_usage': len(re.findall(r'@lru_cache|@cache|memo', code)),
        'deep_recursion_risk': len(re.findall(r'sys\.setrecursionlimit', code))
    }
    
    energy_impact_score = 80  # Base score
    energy_impact_score -= recursion_patterns['recursive_functions'] * 10
    energy_impact_score += recursion_patterns['memoization_usage'] * 15
    energy_impact_score -= recursion_patterns['deep_recursion_risk'] * 20
    
    return {
        'energy_impact_score': max(0, min(100, energy_impact_score)),
        'recursion_patterns': recursion_patterns,
        'stack_overflow_risk': recursion_patterns['deep_recursion_risk'] > 0,
        'optimization_potential': recursion_patterns['recursive_functions'] > recursion_patterns['memoization_usage']
    }


def _analyze_memory_patterns(code: str, language: str) -> Dict[str, Any]:
    """Analyze memory usage patterns."""
    memory_patterns = {
        'large_data_structures': len(re.findall(r'range\s*\(\s*\d{4,}', code)),
        'string_concatenation': len(re.findall(r'\+\s*=\s*["\']', code)),
        'list_copying': len(re.findall(r'list\s*\(|\.copy\s*\(', code)),
        'generator_usage': len(re.findall(r'yield\s+|generator', code)),
        'memory_management': len(re.findall(r'del\s+\w+|gc\.collect', code)),
        'string_join_usage': len(re.findall(r'\.join\s*\(', code))
    }
    
    memory_efficiency_score = 70
    memory_efficiency_score -= memory_patterns['large_data_structures'] * 15
    memory_efficiency_score -= memory_patterns['string_concatenation'] * 8
    memory_efficiency_score -= memory_patterns['list_copying'] * 5
    memory_efficiency_score += memory_patterns['generator_usage'] * 10
    memory_efficiency_score += memory_patterns['memory_management'] * 8
    memory_efficiency_score += memory_patterns['string_join_usage'] * 5
    
    return {
        'memory_efficiency_score': max(0, min(100, memory_efficiency_score)),
        'memory_patterns': memory_patterns,
        'estimated_memory_footprint': _estimate_memory_footprint(memory_patterns),
        'memory_optimization_opportunities': _identify_memory_optimizations(memory_patterns)
    }


def _analyze_cpu_operations(code: str, language: str) -> Dict[str, Any]:
    """Analyze CPU-intensive operations."""
    cpu_intensive_patterns = {
        'mathematical_operations': len(re.findall(r'math\.\w+|numpy\.\w+', code)),
        'regex_operations': len(re.findall(r're\.\w+|regex', code)),
        'file_processing': len(re.findall(r'\.read\(|\.write\(', code)),
        'json_operations': len(re.findall(r'json\.(loads|dumps)', code)),
        'compression_operations': len(re.findall(r'gzip|zip|compress', code)),
        'encryption_operations': len(re.findall(r'hash|encrypt|decrypt', code))
    }
    
    cpu_intensity_score = 50  # Neutral base
    cpu_intensity_score += cpu_intensive_patterns['mathematical_operations'] * 3
    cpu_intensity_score += cpu_intensive_patterns['regex_operations'] * 5
    cpu_intensity_score += cpu_intensive_patterns['file_processing'] * 4
    cpu_intensity_score += cpu_intensive_patterns['json_operations'] * 2
    cpu_intensity_score += cpu_intensive_patterns['compression_operations'] * 8
    cpu_intensity_score += cpu_intensive_patterns['encryption_operations'] * 10
    
    return {
        'cpu_intensity_score': min(200, cpu_intensity_score),  # Higher score means more CPU intensive
        'cpu_patterns': cpu_intensive_patterns,
        'optimization_recommendations': _get_cpu_optimization_recommendations(cpu_intensive_patterns)
    }


def _analyze_io_operations(code: str, language: str) -> Dict[str, Any]:
    """Analyze I/O operations efficiency."""
    io_patterns = {
        'file_operations': len(re.findall(r'open\s*\(|file\s*\(', code)),
        'database_operations': len(re.findall(r'execute\s*\(|query\s*\(', code)),
        'network_requests': len(re.findall(r'requests\.|urllib|http', code)),
        'batch_operations': len(re.findall(r'batch|bulk', code, re.IGNORECASE)),
        'streaming_operations': len(re.findall(r'stream|chunk', code, re.IGNORECASE)),
        'async_operations': len(re.findall(r'async\s+def|await\s+', code))
    }
    
    io_efficiency_score = 60
    io_efficiency_score -= io_patterns['file_operations'] * 3  # I/O is energy expensive
    io_efficiency_score -= io_patterns['database_operations'] * 5
    io_efficiency_score -= io_patterns['network_requests'] * 8
    io_efficiency_score += io_patterns['batch_operations'] * 10  # Batching is efficient
    io_efficiency_score += io_patterns['streaming_operations'] * 8
    io_efficiency_score += io_patterns['async_operations'] * 12  # Async is energy efficient
    
    return {
        'io_efficiency_score': max(0, min(100, io_efficiency_score)),
        'io_patterns': io_patterns,
        'energy_impact': 'high' if io_patterns['network_requests'] > 10 else 'medium' if io_patterns['file_operations'] > 5 else 'low'
    }


def _analyze_network_operations(code: str, language: str) -> Dict[str, Any]:
    """Analyze network operations for energy efficiency."""
    network_patterns = {
        'http_requests': len(re.findall(r'requests\.(get|post|put|delete)', code)),
        'connection_pooling': len(re.findall(r'Session\s*\(|pool', code, re.IGNORECASE)),
        'keep_alive': len(re.findall(r'keep.?alive', code, re.IGNORECASE)),
        'compression_headers': len(re.findall(r'gzip|deflate', code, re.IGNORECASE)),
        'caching_headers': len(re.findall(r'cache.control|etag', code, re.IGNORECASE)),
        'timeout_configuration': len(re.findall(r'timeout\s*=', code))
    }
    
    network_efficiency_score = 50
    network_efficiency_score -= network_patterns['http_requests'] * 5  # Each request consumes energy
    network_efficiency_score += network_patterns['connection_pooling'] * 15
    network_efficiency_score += network_patterns['keep_alive'] * 10
    network_efficiency_score += network_patterns['compression_headers'] * 8
    network_efficiency_score += network_patterns['caching_headers'] * 12
    network_efficiency_score += network_patterns['timeout_configuration'] * 5
    
    return {
        'network_efficiency_score': max(0, min(100, network_efficiency_score)),
        'network_patterns': network_patterns,
        'data_transfer_optimization': network_patterns['compression_headers'] > 0,
        'connection_optimization': network_patterns['connection_pooling'] > 0
    }


def _analyze_database_queries(code: str, language: str) -> Dict[str, Any]:
    """Analyze database query efficiency."""
    db_patterns = {
        'select_queries': len(re.findall(r'SELECT\s+', code, re.IGNORECASE)),
        'select_star': len(re.findall(r'SELECT\s+\*', code, re.IGNORECASE)),
        'where_clauses': len(re.findall(r'WHERE\s+', code, re.IGNORECASE)),
        'joins': len(re.findall(r'(INNER|LEFT|RIGHT|OUTER)\s+JOIN', code, re.IGNORECASE)),
        'indexes_usage': len(re.findall(r'INDEX|index', code, re.IGNORECASE)),
        'bulk_operations': len(re.findall(r'bulk|batch', code, re.IGNORECASE)),
        'pagination': len(re.findall(r'LIMIT|OFFSET|limit|offset', code, re.IGNORECASE))
    }
    
    query_efficiency_score = 70
    query_efficiency_score -= db_patterns['select_star'] * 10  # SELECT * is inefficient
    query_efficiency_score += db_patterns['where_clauses'] * 5  # WHERE clauses are good
    query_efficiency_score -= db_patterns['joins'] * 3  # JOINs can be expensive
    query_efficiency_score += db_patterns['indexes_usage'] * 8
    query_efficiency_score += db_patterns['bulk_operations'] * 12
    query_efficiency_score += db_patterns['pagination'] * 6
    
    return {
        'query_efficiency_score': max(0, min(100, query_efficiency_score)),
        'db_patterns': db_patterns,
        'n_plus_one_risk': db_patterns['select_queries'] > db_patterns['bulk_operations'] * 10,
        'optimization_potential': db_patterns['select_star'] > 0 or db_patterns['joins'] > 5
    }


def _analyze_db_connections(code: str, language: str) -> Dict[str, Any]:
    """Analyze database connection management."""
    connection_patterns = {
        'connection_creation': len(re.findall(r'connect\s*\(|Connection\s*\(', code)),
        'connection_closing': len(re.findall(r'\.close\s*\(|\.disconnect', code)),
        'connection_pooling': len(re.findall(r'pool|Pool', code)),
        'context_managers': len(re.findall(r'with\s+.*connect', code)),
        'transaction_management': len(re.findall(r'commit\s*\(|rollback\s*\(', code))
    }
    
    connection_efficiency_score = 60
    connection_efficiency_score -= connection_patterns['connection_creation'] * 8  # Connection creation is expensive
    connection_efficiency_score += connection_patterns['connection_closing'] * 3
    connection_efficiency_score += connection_patterns['connection_pooling'] * 15
    connection_efficiency_score += connection_patterns['context_managers'] * 10
    connection_efficiency_score += connection_patterns['transaction_management'] * 5
    
    return {
        'connection_efficiency_score': max(0, min(100, connection_efficiency_score)),
        'connection_patterns': connection_patterns,
        'connection_leak_risk': connection_patterns['connection_creation'] > connection_patterns['connection_closing']
    }


def _analyze_data_transfer(code: str, language: str) -> Dict[str, Any]:
    """Analyze data transfer optimization."""
    transfer_patterns = {
        'json_serialization': len(re.findall(r'json\.(dumps|loads)', code)),
        'compression_usage': len(re.findall(r'gzip|compress|zip', code)),
        'streaming_data': len(re.findall(r'stream|chunk|iter', code)),
        'pagination_implementation': len(re.findall(r'page|limit|offset', code, re.IGNORECASE)),
        'binary_formats': len(re.findall(r'pickle|msgpack|protobuf', code)),
        'lazy_loading': len(re.findall(r'lazy|defer', code, re.IGNORECASE))
    }
    
    transfer_efficiency_score = 50
    transfer_efficiency_score += transfer_patterns['compression_usage'] * 12
    transfer_efficiency_score += transfer_patterns['streaming_data'] * 10
    transfer_efficiency_score += transfer_patterns['pagination_implementation'] * 8
    transfer_efficiency_score += transfer_patterns['binary_formats'] * 8
    transfer_efficiency_score += transfer_patterns['lazy_loading'] * 10
    
    return {
        'transfer_efficiency_score': min(100, transfer_efficiency_score),
        'transfer_patterns': transfer_patterns,
        'bandwidth_optimization': transfer_patterns['compression_usage'] > 0,
        'memory_optimization': transfer_patterns['streaming_data'] > 0
    }


def _analyze_caching_strategies(code: str, language: str) -> Dict[str, Any]:
    """Analyze caching strategies implementation."""
    caching_patterns = {
        'function_caching': len(re.findall(r'@lru_cache|@cache', code)),
        'redis_caching': len(re.findall(r'redis|Redis', code)),
        'memcached_usage': len(re.findall(r'memcached|Memcached', code)),
        'in_memory_caching': len(re.findall(r'cache.*dict|dict.*cache', code, re.IGNORECASE)),
        'http_caching': len(re.findall(r'cache.control|etag|expires', code, re.IGNORECASE)),
        'database_caching': len(re.findall(r'query.*cache|cache.*query', code, re.IGNORECASE))
    }
    
    caching_efficiency_score = sum(caching_patterns.values()) * 15
    caching_efficiency_score = min(100, caching_efficiency_score)
    
    return {
        'caching_efficiency_score': caching_efficiency_score,
        'caching_patterns': caching_patterns,
        'has_caching_strategy': sum(caching_patterns.values()) > 0,
        'multi_level_caching': len([v for v in caching_patterns.values() if v > 0]) > 2
    }


def _analyze_lazy_loading(code: str, language: str) -> Dict[str, Any]:
    """Analyze lazy loading implementation."""
    lazy_patterns = {
        'lazy_imports': len(re.findall(r'importlib|__import__', code)),
        'lazy_evaluation': len(re.findall(r'lazy|defer', code, re.IGNORECASE)),
        'generator_usage': len(re.findall(r'yield\s+|generator', code)),
        'property_lazy': len(re.findall(r'@property.*lazy|@lazy.*property', code, re.IGNORECASE)),
        'conditional_loading': len(re.findall(r'if.*load|load.*if', code, re.IGNORECASE))
    }
    
    lazy_loading_score = sum(lazy_patterns.values()) * 20
    lazy_loading_score = min(100, lazy_loading_score)
    
    return {
        'lazy_loading_score': lazy_loading_score,
        'lazy_patterns': lazy_patterns,
        'resource_optimization': sum(lazy_patterns.values()) > 2
    }


def _analyze_compression_usage(code: str, language: str) -> Dict[str, Any]:
    """Analyze data compression usage."""
    compression_patterns = {
        'gzip_compression': len(re.findall(r'gzip', code, re.IGNORECASE)),
        'zip_compression': len(re.findall(r'zipfile|zip', code, re.IGNORECASE)),
        'json_compression': len(re.findall(r'compress.*json|json.*compress', code, re.IGNORECASE)),
        'image_optimization': len(re.findall(r'PIL|Pillow|optimize', code, re.IGNORECASE)),
        'text_compression': len(re.findall(r'lzma|bz2', code, re.IGNORECASE))
    }
    
    compression_score = sum(compression_patterns.values()) * 20
    compression_score = min(100, compression_score)
    
    return {
        'compression_score': compression_score,
        'compression_patterns': compression_patterns,
        'bandwidth_savings': compression_score > 40,
        'storage_savings': compression_score > 20
    }


def _analyze_resource_pooling(code: str, language: str) -> Dict[str, Any]:
    """Analyze resource pooling implementation."""
    pooling_patterns = {
        'connection_pooling': len(re.findall(r'pool|Pool', code)),
        'thread_pooling': len(re.findall(r'ThreadPool|ProcessPool', code)),
        'object_pooling': len(re.findall(r'ObjectPool|object.*pool', code, re.IGNORECASE)),
        'memory_pooling': len(re.findall(r'memory.*pool|pool.*memory', code, re.IGNORECASE))
    }
    
    pooling_score = sum(pooling_patterns.values()) * 25
    pooling_score = min(100, pooling_score)
    
    return {
        'pooling_score': pooling_score,
        'pooling_patterns': pooling_patterns,
        'resource_reuse': pooling_score > 25
    }


def _identify_energy_patterns(code: str, language: str) -> Dict[str, Any]:
    """Identify energy-efficient patterns."""
    energy_patterns = {
        'async_programming': len(re.findall(r'async\s+def|await\s+', code)),
        'event_driven': len(re.findall(r'event|callback|trigger', code, re.IGNORECASE)),
        'microservices_patterns': len(re.findall(r'service|api|endpoint', code, re.IGNORECASE)),
        'serverless_patterns': len(re.findall(r'lambda|function|serverless', code, re.IGNORECASE)),
        'green_algorithms': len(re.findall(r'efficient|optimize|green', code, re.IGNORECASE))
    }
    
    energy_efficiency_score = 40  # Base score
    energy_efficiency_score += energy_patterns['async_programming'] * 15
    energy_efficiency_score += energy_patterns['event_driven'] * 10
    energy_efficiency_score += energy_patterns['microservices_patterns'] * 5
    energy_efficiency_score += energy_patterns['serverless_patterns'] * 12
    energy_efficiency_score += energy_patterns['green_algorithms'] * 3
    
    return {
        'energy_efficiency_score': min(100, energy_efficiency_score),
        'energy_patterns': energy_patterns,
        'async_utilization': energy_patterns['async_programming'] > 0,
        'scalability_patterns': energy_patterns['microservices_patterns'] > 3
    }


def _analyze_carbon_practices(code: str, language: str) -> Dict[str, Any]:
    """Analyze carbon-aware programming practices."""
    carbon_practices = {
        'monitoring_metrics': len(re.findall(r'monitor|metric|measure', code, re.IGNORECASE)),
        'resource_scheduling': len(re.findall(r'schedule|queue|priority', code, re.IGNORECASE)),
        'power_management': len(re.findall(r'power|energy|battery', code, re.IGNORECASE)),
        'carbon_optimization': len(re.findall(r'carbon|green|sustainable', code, re.IGNORECASE)),
        'efficient_deployment': len(re.findall(r'container|docker|kubernetes', code, re.IGNORECASE))
    }
    
    carbon_awareness_score = sum(carbon_practices.values()) * 20
    carbon_awareness_score = min(100, carbon_awareness_score)
    
    return {
        'carbon_awareness_score': carbon_awareness_score,
        'carbon_practices': carbon_practices,
        'has_monitoring': carbon_practices['monitoring_metrics'] > 0,
        'deployment_efficiency': carbon_practices['efficient_deployment'] > 0
    }


def _assess_sustainable_patterns(code: str, language: str) -> Dict[str, Any]:
    """Assess sustainable architecture patterns."""
    sustainable_patterns = {
        'modular_design': len(re.findall(r'module|component|service', code, re.IGNORECASE)),
        'reusable_code': len(re.findall(r'reuse|util|helper|common', code, re.IGNORECASE)),
        'configuration_driven': len(re.findall(r'config|setting|env', code, re.IGNORECASE)),
        'documentation': len(re.findall(r'""".*"""', code, re.DOTALL)),
        'testing': len(re.findall(r'test|Test|assert', code))
    }
    
    sustainability_score = 30  # Base score
    sustainability_score += min(sustainable_patterns['modular_design'] * 8, 25)
    sustainability_score += min(sustainable_patterns['reusable_code'] * 6, 20)
    sustainability_score += min(sustainable_patterns['configuration_driven'] * 5, 15)
    sustainability_score += min(sustainable_patterns['documentation'] * 3, 10)
    
    return {
        'sustainability_score': min(100, sustainability_score),
        'sustainable_patterns': sustainable_patterns,
        'maintainability_focus': sustainability_score > 70,
        'long_term_viability': sustainable_patterns['documentation'] > 3 and sustainable_patterns['testing'] > 0
    }


# Helper functions for calculations and estimates

def _estimate_cpu_cycles(complexity_indicators: Dict[str, int]) -> int:
    """Estimate relative CPU cycles based on complexity indicators."""
    base_cycles = 1000
    cycles = base_cycles
    
    cycles += complexity_indicators['nested_loops'] * 10000
    cycles += complexity_indicators['triple_nested_loops'] * 100000
    cycles += complexity_indicators['while_loops'] * 5000
    cycles += complexity_indicators['recursive_functions'] * 15000
    cycles += complexity_indicators['sorting_operations'] * 8000
    
    return cycles


def _get_loop_recommendations(loop_patterns: Dict[str, int]) -> List[str]:
    """Get loop optimization recommendations."""
    recommendations = []
    
    if loop_patterns['inefficient_loops'] > 0:
        recommendations.append("Replace range(len()) loops with direct iteration")
    if loop_patterns['list_comprehensions'] == 0 and loop_patterns['map_filter_usage'] == 0:
        recommendations.append("Consider using list comprehensions or map/filter for better performance")
    if loop_patterns['generator_expressions'] == 0:
        recommendations.append("Use generator expressions for memory-efficient iteration")
    
    return recommendations


def _rate_memory_efficiency(data_structure_usage: Dict[str, int]) -> str:
    """Rate memory efficiency based on data structure usage."""
    efficient_structures = data_structure_usage['sets'] + data_structure_usage['deque_usage'] + data_structure_usage['defaultdict_usage']
    total_structures = sum(data_structure_usage.values())
    
    if total_structures == 0:
        return 'unknown'
    
    efficiency_ratio = efficient_structures / total_structures
    
    if efficiency_ratio > 0.7:
        return 'excellent'
    elif efficiency_ratio > 0.4:
        return 'good'
    elif efficiency_ratio > 0.2:
        return 'fair'
    else:
        return 'poor'


def _estimate_memory_footprint(memory_patterns: Dict[str, int]) -> str:
    """Estimate relative memory footprint."""
    footprint_score = 0
    footprint_score += memory_patterns['large_data_structures'] * 100
    footprint_score += memory_patterns['string_concatenation'] * 20
    footprint_score += memory_patterns['list_copying'] * 30
    footprint_score -= memory_patterns['generator_usage'] * 50
    
    if footprint_score > 500:
        return 'very_high'
    elif footprint_score > 200:
        return 'high'
    elif footprint_score > 50:
        return 'medium'
    else:
        return 'low'


def _identify_memory_optimizations(memory_patterns: Dict[str, int]) -> List[str]:
    """Identify memory optimization opportunities."""
    optimizations = []
    
    if memory_patterns['string_concatenation'] > 3:
        optimizations.append("Use str.join() instead of string concatenation in loops")
    if memory_patterns['large_data_structures'] > 0:
        optimizations.append("Consider using generators or iterators for large datasets")
    if memory_patterns['list_copying'] > 2:
        optimizations.append("Minimize list copying operations")
    if memory_patterns['generator_usage'] == 0:
        optimizations.append("Implement generators for memory-efficient data processing")
    
    return optimizations


def _get_cpu_optimization_recommendations(cpu_patterns: Dict[str, int]) -> List[str]:
    """Get CPU optimization recommendations."""
    recommendations = []
    
    if cpu_patterns['regex_operations'] > 5:
        recommendations.append("Consider compiling regex patterns for better performance")
    if cpu_patterns['json_operations'] > 10:
        recommendations.append("Use faster JSON libraries like orjson or ujson")
    if cpu_patterns['mathematical_operations'] > 10:
        recommendations.append("Consider using NumPy for vectorized mathematical operations")
    if cpu_patterns['encryption_operations'] > 3:
        recommendations.append("Implement caching for expensive cryptographic operations")
    
    return recommendations


def _calculate_environmental_impact(carbon_result: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall environmental impact assessment."""
    scores = {
        'computational_efficiency': carbon_result['computational_efficiency']['algorithm_complexity']['complexity_score'],
        'resource_consumption': 100 - carbon_result['resource_consumption']['cpu_intensive_operations']['cpu_intensity_score'],
        'database_efficiency': carbon_result['database_efficiency']['query_optimization']['query_efficiency_score'],
        'caching_optimization': carbon_result['caching_and_optimization']['caching_strategies']['caching_efficiency_score'],
        'green_practices': carbon_result['green_software_practices']['energy_efficient_patterns']['energy_efficiency_score']
    }
    
    overall_score = sum(scores.values()) / len(scores)
    
    # Calculate estimated energy consumption (relative scale)
    energy_consumption = 'low'
    if overall_score < 40:
        energy_consumption = 'very_high'
    elif overall_score < 55:
        energy_consumption = 'high'
    elif overall_score < 70:
        energy_consumption = 'medium'
    elif overall_score < 85:
        energy_consumption = 'low'
    else:
        energy_consumption = 'very_low'
    
    return {
        'overall_environmental_score': round(overall_score, 2),
        'environmental_grade': _get_environmental_grade(overall_score),
        'estimated_energy_consumption': energy_consumption,
        'carbon_footprint_rating': _get_carbon_rating(overall_score),
        'impact_areas': scores,
        'sustainability_metrics': {
            'code_efficiency': overall_score,
            'resource_optimization': scores['resource_consumption'],
            'green_practices_adoption': scores['green_practices']
        }
    }


def _calculate_green_score(carbon_result: Dict[str, Any]) -> int:
    """Calculate overall green software score."""
    impact_assessment = carbon_result['environmental_impact_assessment']
    return int(impact_assessment['overall_environmental_score'])


def _generate_green_recommendations(carbon_result: Dict[str, Any]) -> List[str]:
    """Generate green software recommendations."""
    recommendations = []
    
    # Algorithm efficiency recommendations
    if carbon_result['computational_efficiency']['algorithm_complexity']['complexity_score'] < 60:
        recommendations.append("Optimize algorithm complexity to reduce CPU cycles and energy consumption")
    
    # Caching recommendations
    if not carbon_result['caching_and_optimization']['caching_strategies']['has_caching_strategy']:
        recommendations.append("Implement caching strategies to reduce redundant computations")
    
    # Database efficiency recommendations
    if carbon_result['database_efficiency']['query_optimization']['optimization_potential']:
        recommendations.append("Optimize database queries to reduce energy consumption")
    
    # I/O efficiency recommendations
    if carbon_result['resource_consumption']['io_operations']['energy_impact'] == 'high':
        recommendations.append("Minimize I/O operations and implement batch processing")
    
    # Async programming recommendations
    if not carbon_result['green_software_practices']['energy_efficient_patterns']['async_utilization']:
        recommendations.append("Consider async programming patterns for better energy efficiency")
    
    # Memory optimization recommendations
    memory_optimizations = carbon_result['resource_consumption']['memory_usage_patterns']['memory_optimization_opportunities']
    recommendations.extend(memory_optimizations)
    
    # Network optimization recommendations
    if not carbon_result['resource_consumption']['network_efficiency']['data_transfer_optimization']:
        recommendations.append("Implement data compression to reduce network energy consumption")
    
    if not recommendations:
        recommendations.append("Code demonstrates good green software practices - maintain current efficiency standards")
    
    return recommendations


def _get_environmental_grade(score: float) -> str:
    """Convert environmental score to grade."""
    if score >= 85:
        return 'A'
    elif score >= 70:
        return 'B'
    elif score >= 55:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'


def _get_carbon_rating(score: float) -> str:
    """Get carbon footprint rating."""
    if score >= 85:
        return 'very_low'
    elif score >= 70:
        return 'low'
    elif score >= 55:
        return 'moderate'
    elif score >= 40:
        return 'high'
    else:
        return 'very_high'