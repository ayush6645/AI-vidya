# backend/routes/logout_route.py

from flask import Blueprint, session, redirect, url_for, flash

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/logout')
def logout_user():
    # Clear the user's session data
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('login.login'))