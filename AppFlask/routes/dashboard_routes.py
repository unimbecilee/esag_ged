from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
from AppFlask.db import db_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    return render_template('dashboard.html')

@dashboard_bp.route('/dashboard/preferences', methods=['GET', 'POST'])
def manage_preferences():
    user_id = session.get('user_id')

    if not user_id:
        flash("Vous devez être connecté pour accéder aux préférences")
        return redirect(url_for('auth.login'))

    conn = db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        dark_mode = request.form.get('dark_mode') == 'on'
        preferences = {"dark_mode": dark_mode}

        update_query = """
            INSERT INTO TableauDeBord (utilisateur_id, preferences)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE preferences = VALUES(preferences)
        """
        cursor.execute(update_query, (user_id, json.dumps(preferences)))
        conn.commit()
        flash("Préférences mises à jour avec succès")

    cursor.execute("SELECT preferences FROM TableauDeBord WHERE utilisateur_id = %s", (user_id,))
    result = cursor.fetchone()
    preferences = result['preferences'] if result else {}

    cursor.close()
    conn.close()

    return render_template('preferences.html', preferences=preferences)
