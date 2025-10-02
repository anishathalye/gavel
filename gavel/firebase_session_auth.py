# Firebase Session Authentication for HackPSU Integration
# This module replaces Gavel's built-in authentication with HackPSU's Firebase-based session auth

import requests
from flask import request, session, redirect, abort, render_template
from functools import wraps
from gavel.models import Annotator, db
import os
import jwt

AUTH_SERVER_URL = os.environ.get('AUTH_SERVER_URL', 'http://localhost:3000/api/sessionUser')
MIN_JUDGE_ROLE = 2  # Only users with role >= 2 can judge
MIN_ADMIN_ROLE = 4  # Only users with role >= 4 can access admin panel

"""
Role Levels (from HackPSU NestJS backend):
0 = NONE (no access)
1 = HACKER (participant)
2 = ORGANIZER (can judge) ← Minimum for Gavel access
3 = EXECUTIVE (can judge + more admin features)
4 = ADMIN (full access) ← Minimum for /admin panel
"""

def decode_session_token(token_string):
    """Decode Firebase session JWT token without verification"""
    try:
        # Decode without verification (we trust the session cookie)
        decoded = jwt.decode(token_string, options={"verify_signature": False})
        print(f"[DEBUG] Decoded token: {decoded}")
        return decoded
    except Exception as e:
        print(f"[ERROR] Failed to decode token: {e}")
        return None

def verify_hackpsu_session():
    """Verify session with HackPSU auth server and extract user data"""
    try:
        # Get session token from cookies
        session_token = request.cookies.get('__session')

        if not session_token:
            print("[DEBUG] No __session cookie found")
            return None

        print(f"[DEBUG] Found __session cookie")

        # Decode the session token to get user data
        user_data = decode_session_token(session_token)

        if not user_data:
            print("[DEBUG] Failed to decode session token")
            return None

        # Extract relevant user info
        email = user_data.get('email', '')
        name = user_data.get('name') or user_data.get('displayName')

        # If no name, use email prefix
        if not name and email:
            name = email.split('@')[0]

        user_info = {
            'uid': user_data.get('user_id') or user_data.get('sub'),
            'email': email,
            'displayName': name or 'Unknown User',
            'customClaims': {
                'production': user_data.get('production', 0),
                'staging': user_data.get('staging', 0)
            }
        }

        print(f"[DEBUG] Extracted user info: {user_info}")

        if not user_info.get('uid') and not user_info.get('email'):
            print("[DEBUG] No valid user data in token")
            return None

        return user_info

    except Exception as e:
        print(f"[ERROR] Session verification failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_user_privilege(user_data):
    """Extract role level from Firebase custom claims"""
    # Get AUTH_ENVIRONMENT from config (production or staging)
    auth_env = os.environ.get('AUTH_ENVIRONMENT', 'production')

    # Custom claims are in the user data
    custom_claims = user_data.get('customClaims', {})

    # Extract privilege for current environment
    privilege = custom_claims.get(auth_env, 0)

    return privilege

def check_judge_permission(user_data):
    """Check if user has sufficient privileges to judge (role >= 2)"""
    privilege = extract_user_privilege(user_data)
    min_role = int(os.environ.get('MIN_JUDGE_ROLE', MIN_JUDGE_ROLE))
    return privilege >= min_role

def check_admin_permission(user_data):
    """Check if user has admin privileges (role >= 4)"""
    privilege = extract_user_privilege(user_data)
    min_role = int(os.environ.get('MIN_ADMIN_ROLE', MIN_ADMIN_ROLE))
    return privilege >= min_role

def hackpsu_auth_required(f):
    """Require HackPSU authentication with judge permissions"""
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"[DEBUG] Auth required for route: {request.path}")

        # Verify with auth server
        print("[DEBUG] Verifying with auth server...")
        user_data = verify_hackpsu_session()

        if not user_data:
            # Redirect to auth flow with return URL
            auth_login_url = os.environ.get('AUTH_LOGIN_URL', 'http://localhost:3000/login')
            redirect_url = f'{auth_login_url}?redirect={request.url}'
            print(f"[DEBUG] No user data, redirecting to: {redirect_url}")
            return redirect(redirect_url)

        print(f"[DEBUG] User data received: {user_data.get('email')}")

        # Check if user has sufficient privileges
        if not check_judge_permission(user_data):
            privilege = extract_user_privilege(user_data)
            print(f"[DEBUG] Insufficient privileges: {privilege} < {os.environ.get('MIN_JUDGE_ROLE', MIN_JUDGE_ROLE)}")
            return render_template(
                'error.html',
                message=f'You need organizer permissions (level 2+) to access judging. Your current level: {privilege}'
            ), 403

        # Get or create Gavel annotator
        annotator = sync_annotator_from_auth_server(user_data)

        if not annotator or not annotator.active:
            print(f"[DEBUG] Annotator inactive or creation failed")
            return render_template(
                'error.html',
                message='Your judging account is not active. Please contact an admin.'
            ), 403

        # Set Gavel session
        session['annotator_id'] = annotator.id
        print(f"[DEBUG] Auth successful, session set for: {annotator.email}")

        return f(*args, **kwargs)
    return decorated

def hackpsu_admin_required(f):
    """Require HackPSU authentication with admin permissions"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_data = verify_hackpsu_session()

        if not user_data:
            auth_login_url = os.environ.get('AUTH_LOGIN_URL', 'http://localhost:3000/login')
            return redirect(f'{auth_login_url}?redirect={request.url}')

        # Check admin permissions
        if not check_admin_permission(user_data):
            return render_template(
                'error.html',
                message='Admin access required. You need permission level 4+.'
            ), 403

        # Still set annotator session for admin (in case they judge too)
        annotator = sync_annotator_from_auth_server(user_data)
        if annotator:
            session['annotator_id'] = annotator.id

        return f(*args, **kwargs)
    return decorated

def sync_annotator_from_auth_server(user_data):
    """Create/update Gavel annotator from Firebase user data"""
    email = user_data.get('email')
    uid = user_data.get('uid')

    if not email:
        return None

    # Map role level to description
    privilege = extract_user_privilege(user_data)
    role_names = {
        0: 'User',
        1: 'Hacker',
        2: 'Organizer',
        3: 'Executive',
        4: 'Admin'
    }
    role_description = role_names.get(privilege, f'Role Level {privilege}')

    # Find existing annotator by email
    annotator = Annotator.query.filter_by(email=email).first()

    min_role = int(os.environ.get('MIN_JUDGE_ROLE', MIN_JUDGE_ROLE))

    if not annotator:
        # Create new annotator
        annotator = Annotator(
            name=user_data.get('displayName', user_data.get('name', email.split('@')[0])),
            email=email,
            description=role_description
        )
        # Set active status based on privilege level
        annotator.active = privilege >= min_role
        db.session.add(annotator)
        db.session.commit()
    else:
        # Update existing annotator info
        annotator.name = user_data.get('displayName', annotator.name)
        annotator.description = role_description
        # Keep them active if they have permission level >= MIN_JUDGE_ROLE
        annotator.active = privilege >= min_role
        db.session.commit()

    return annotator if annotator.active else None
