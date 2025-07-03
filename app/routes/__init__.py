# routes package init 
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html') 
    
@main_bp.route('/recongntine')
def recongntine():
    return render_template('ai_recongntine.html')     