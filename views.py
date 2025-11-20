from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import create_note, get_notes, find_note, update_note, soft_delete, restore, permanent_delete, find_user, update_user, get_notes as _get_notes
from datetime import datetime, timedelta
from functools import wraps
import random

main_bp = Blueprint('main', __name__)

@main_bp.after_app_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user'): 
            flash('Login required','warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper

@main_bp.route('/')
@login_required
def home():
    username = session.get('user')
    notes = [n for n in _get_notes() if n.get('owner') == username and n.get('status') == 'active']
    return render_template('home.html', notes=notes)

@main_bp.route('/archive')
@login_required
def archive():
    username = session.get('user')
    archived_notes = [n for n in _get_notes() if n.get('owner') == username and n.get('status') == 'archived']
    return render_template('archive.html', archived_notes=archived_notes)

@main_bp.route('/note/add', methods=['POST'])
@login_required
def add_note():
    title = request.form.get('title')
    content = request.form.get('content')
    if not title: 
        flash('Title required','danger')
        return redirect(url_for('main.home'))
    create_note(session.get('user'), title, content)
    flash('Note added','success')
    return redirect(url_for('main.home'))

@main_bp.route('/note/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = find_note(note_id) 
    
    if not note or note.get('owner') != session.get('user'):
        flash('Note not found or unauthorized.','danger')
        return redirect(url_for('main.home'))

    if note.get('status') == 'active':
        soft_delete(note_id)
        flash('Note archived successfully!','info')
        return redirect(url_for('main.home'))
    
    elif note.get('status') == 'archived':
        permanent_delete(note_id)
        flash('Note permanently deleted.','warning')
        return redirect(url_for('main.archive'))
        
    return redirect(url_for('main.home'))

@main_bp.route('/note/restore/<int:note_id>', methods=['POST'])
@login_required
def restore_note(note_id):
    note = find_note(note_id)
    
    if not note or note.get('owner') != session.get('user'):
        flash('Note not found or unauthorized.','danger')
        return redirect(url_for('main.archive'))
    
    restore(note_id)
    flash('Note restored to active list!','success')
    return redirect(url_for('main.home'))

@main_bp.route('/note/edit/<int:note_id>', methods=['GET','POST'])
@login_required
def edit_note(note_id):
    note = find_note(note_id)
    
    if not note or note.get('owner') != session.get('user'):
        flash('Note not found or unauthorized.','danger')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title: 
            flash('Title required','danger')
            return redirect(url_for('main.edit_note', note_id=note_id))
        update_note(note_id, {'title': title, 'content': content})
        flash('Note updated','success')
        return redirect(url_for('main.home'))
        
    return render_template('edit_note.html', note=note)

@main_bp.route('/profile')
@login_required
def profile():
    user = find_user(session.get('user'))
    return render_template('profile.html', user=user)

@main_bp.route('/profile/edit', methods=['GET','POST'])
@login_required
def edit_profile():
    user = find_user(session.get('user'))
    
    if request.method == 'POST':
        # Check if this is OTP verification request
        if request.form.get('action') == 'verify_otp':
            otp = request.form.get('otp')
            stored_otp = session.get('profile_otp')
            expires = session.get('profile_otp_expires')
            
            # Verify OTP
            if not stored_otp or not expires:
                flash('OTP session expired. Please request new OTP.', 'danger')
                return redirect(url_for('main.edit_profile'))
            
            if datetime.utcnow() > datetime.fromisoformat(expires):
                session.pop('profile_otp', None)
                session.pop('profile_otp_expires', None)
                flash('OTP expired. Please request new OTP.', 'danger')
                return redirect(url_for('main.edit_profile'))
            
            if otp != stored_otp:
                flash('Invalid OTP.', 'danger')
                return redirect(url_for('main.edit_profile'))
            
            # OTP verified successfully - now process profile update
            data = request.form
            
            # Basic validation
            if not data.get('first_name') or not data.get('last_name') or not data.get('email'):
                flash('Please fill all required fields.', 'danger')
                return redirect(url_for('main.edit_profile'))
            
            # Prepare updates
            updates = {
                'first_name': data.get('first_name'),
                'middle_name': data.get('middle_name'),
                'last_name': data.get('last_name'),
                'contact': data.get('contact_number'),
                'email': data.get('email')
            }
            
            if data.get('city_municipality') and data.get('barangay') and data.get('zip_code'):
                address_string = f"{data.get('barangay')}, {data.get('city_municipality')}, Laguna, {data.get('zip_code')}"
                updates['address'] = address_string
            
            update_user(session.get('user'), updates)
            
            # Clear OTP session after successful update
            session.pop('profile_otp', None)
            session.pop('profile_otp_expires', None)
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.profile'))
        
        # If regular form submission (without OTP), handle normally
        data = request.form
        
        # Basic validation
        if not data.get('first_name') or not data.get('last_name') or not data.get('email'):
            flash('Please fill all required fields.', 'danger')
            return render_template('edit_profile.html', user=user)
        
        # Prepare updates
        updates = {
            'first_name': data.get('first_name'),
            'middle_name': data.get('middle_name'),
            'last_name': data.get('last_name'),
            'contact': data.get('contact_number'),
            'email': data.get('email')
        }
        
        if data.get('city_municipality') and data.get('barangay') and data.get('zip_code'):
            address_string = f"{data.get('barangay')}, {data.get('city_municipality')}, Laguna, {data.get('zip_code')}"
            updates['address'] = address_string
        
        update_user(session.get('user'), updates)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('edit_profile.html', user=user)

@main_bp.route('/profile/send-otp', methods=['POST'])
@login_required
def profile_send_otp():
    otp = '{:06d}'.format(random.randint(0, 999999))
    session['profile_otp'] = otp
    session['profile_otp_expires'] = (datetime.utcnow() + timedelta(minutes=3)).isoformat()
    
    return jsonify({
        'status': 'success', 
        'message': f'OTP sent for profile changes: {otp} — expires in 3 minutes',
        'otp': otp  # For demo purposes
    })