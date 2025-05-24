from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

# Créez un Blueprint pour les routes de workflow
workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

@workflow_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_workflow():
    if request.method == 'POST':
        # Logique de création de workflow ici
        # Par exemple, récupérer les données du formulaire:
        # workflow_name = request.form.get('workflow_name')
        # ... autres champs ...
        flash('Workflow créé avec succès!', 'success') # Exemple de message flash
        return redirect(url_for('dashboard.manage_preferences')) # Rediriger vers une page appropriée
    return render_template('workflow/create_workflow.html')

# Vous pouvez ajouter d'autres routes liées aux workflows ici
# Par exemple, pour lister les workflows, les modifier, les supprimer, etc.