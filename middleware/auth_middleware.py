from functools import wraps
from flask import request, jsonify
from services.auth_service import SupabaseAuthService

def require_auth(f):
    """
    Decorator to require authentication for routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'Authorization header missing'
            }), 401
        
        try:
            # Extract token from "Bearer <token>" format
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
            
            auth_service = SupabaseAuthService()
            user_data = auth_service.verify_token(token)
            
            if not user_data.get('is_authenticated'):
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired token'
                }), 401
            
            # Add user data to request context
            request.user = user_data
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Authentication failed'
            }), 401
    
    return decorated_function

def require_admin(f):
    """
    Decorator to require admin authentication for routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'Authorization header missing'
            }), 401
        
        try:
            # Extract token from "Bearer <token>" format
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
            
            auth_service = SupabaseAuthService()
            user_data = auth_service.verify_token(token)
            
            if not user_data.get('is_authenticated'):
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired token'
                }), 401
            
            # Check if user is admin (you can implement your own admin logic here)
            # For now, we'll check if the email contains 'admin' or is a specific admin email
            email = user_data.get('email', '').lower()
            if 'admin' not in email and email != 'admin@storycatcher.com':
                return jsonify({
                    'success': False,
                    'error': 'Admin access required'
                }), 403
            
            # Add user data to request context
            request.user = user_data
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Authentication failed'
            }), 401
    
    return decorated_function
