import os
from supabase import create_client, Client
from jose import jwt, JWTError
from datetime import datetime, timedelta
import requests

class SupabaseAuthService:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and return user data
        """
        try:
            # Verify token with Supabase
            response = self.supabase.auth.get_user(token)
            if response.user:
                return {
                    'user_id': response.user.id,
                    'email': response.user.email,
                    'is_authenticated': True
                }
            return {'is_authenticated': False}
        except Exception as e:
            print(f"Token verification error: {e}")
            return {'is_authenticated': False}
    
    def get_user_by_id(self, user_id: str) -> dict:
        """
        Get user data by user ID
        """
        try:
            response = self.supabase.auth.admin.get_user_by_id(user_id)
            if response.user:
                return {
                    'user_id': response.user.id,
                    'email': response.user.email,
                    'created_at': response.user.created_at,
                    'last_sign_in': response.user.last_sign_in_at
                }
            return None
        except Exception as e:
            print(f"Get user error: {e}")
            return None
    
    def create_user(self, email: str, password: str) -> dict:
        """
        Create a new user
        """
        try:
            response = self.supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True
            })
            if response.user:
                return {
                    'success': True,
                    'user_id': response.user.id,
                    'email': response.user.email
                }
            return {'success': False, 'error': 'Failed to create user'}
        except Exception as e:
            print(f"Create user error: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_user(self, user_id: str) -> dict:
        """
        Delete a user
        """
        try:
            response = self.supabase.auth.admin.delete_user(user_id)
            return {'success': True}
        except Exception as e:
            print(f"Delete user error: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_users(self) -> dict:
        """
        List all users
        """
        try:
            response = self.supabase.auth.admin.list_users()
            users = []
            for user in response:
                users.append({
                    'user_id': user.id,
                    'email': user.email,
                    'created_at': user.created_at,
                    'last_sign_in': user.last_sign_in_at
                })
            return {'success': True, 'users': users}
        except Exception as e:
            print(f"List users error: {e}")
            return {'success': False, 'error': str(e)}
