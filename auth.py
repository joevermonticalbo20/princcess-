from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import find_user, add_user, hash_password, verify_password, update_user, find_user_by_email, find_user_by_contact
from datetime import datetime, timedelta
import random
import re

auth_bp = Blueprint('auth', __name__)

# Helper function to validate email domain
def is_valid_email_domain(email):
    """Validate email has a complete domain with proper TLD"""
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    # Extract domain part
    domain = email.split('@')[1]
    
    # Check for common incomplete domains
    incomplete_patterns = [
        r'\.c$',      # ends with .c
        r'\.co$',     # ends with .co  
        r'\.cm$',     # ends with .cm
        r'\.om$',     # ends with .om
        r'\.[a-z]$',  # single letter TLD
        r'\s',        # contains spaces
        r'\.gmail$',  # missing TLD
        r'\.yahoo$',  # missing TLD
        r'\.hotmail$', # missing TLD
    ]
    
    for incomplete_pattern in incomplete_patterns:
        if re.search(incomplete_pattern, domain, re.IGNORECASE):
            return False
    
    # Check for valid TLD length
    tld = domain.split('.')[-1]
    if len(tld) < 2:
        return False
    
    return True

# Helper function to validate strong password
def is_strong_password(password):
    """
    Validate strong password requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter  
    - At least one number
    - At least one special character
    - Only allowed characters: A-Z, a-z, 0-9, and special characters !@#$%^&*()_+-=[]{}|;:,.<>?
    - No spaces or other invalid characters
    """
    # Check for invalid characters first - only allow chars, numbers, and special chars
    if not re.match(r'^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]+$', password):
        return False, "Password can only contain letters, numbers, and special characters"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

# Registration Route (Updated with all validations)
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        
        # Required fields
        required = [
            'first_name', 'last_name', 'date_of_birth', 'contact_number',
            'username', 'email', 'password', 'confirm_password',
            'city_municipality', 'barangay', 'zip_code'
        ]

        # 1. Check for missing fields
        for r in required:
            if not data.get(r):
                flash('Please fill all required fields.', 'danger')
                return render_template('register.html', form_data=data)
        
        # 2. Password strength validation
        password = data.get('password')
        is_strong, strength_message = is_strong_password(password)
        if not is_strong:
            flash(strength_message, 'danger')
            return render_template('register.html', form_data=data)
        
        # 3. Password mismatch check
        if password != data.get('confirm_password'):
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', form_data=data)
        
        # 4. Username existence check
        if find_user(data.get('username')):
            flash('Username already exists.', 'danger')
            return render_template('register.html', form_data=data)
        
        # 5. Email validation and existence check
        email = data.get('email').strip().lower()
        if not is_valid_email_domain(email):
            flash('Please enter a complete email address with proper domain (e.g., user@gmail.com not user@gmail.cm).', 'danger')
            return render_template('register.html', form_data=data)
        
        if find_user_by_email(email):
            flash('Email address already registered.', 'danger')
            return render_template('register.html', form_data=data)
        
        # 6. Contact number validation and existence check - FIXED
        contact_number = data.get('contact_number').strip()
        
        # Remove spaces, dashes, and normalize
        contact_number_clean = re.sub(r'[\s\-+]', '', contact_number)
        
        # Validate Philippine mobile number format
        if not (contact_number_clean.startswith('09') and len(contact_number_clean) == 11 and contact_number_clean.isdigit()):
            flash('Please enter a valid Philippine contact number (09xxxxxxxxx format, 11 digits).', 'danger')
            return render_template('register.html', form_data=data)
        
        # Check for repetitive numbers (like 09111111111)
        digits = contact_number_clean[2:]  # Remove the '09' prefix
        if len(set(digits)) <= 2:  # If only 1-2 unique digits in the remaining 9 digits
            flash('Invalid contact number. Avoid repetitive digits.', 'danger')
            return render_template('register.html', form_data=data)
        
        if find_user_by_contact(contact_number_clean):
            flash('Contact number already registered.', 'danger')
            return render_template('register.html', form_data=data)
        
        # 7. Age/DOB validation and calculation
        dob_str = data.get('date_of_birth')
        try:
            dob = datetime.fromisoformat(dob_str)
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('register.html', form_data=data)
        
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18 or age > 100:
            flash('Must be between 18 and 100 years old to register.', 'danger')
            return render_template('register.html', form_data=data)

        # 8. Address Formation
        address_string = f"{data.get('barangay')}, {data.get('city_municipality')}, Laguna, {data.get('zip_code')}"

        # 9. Prepare user data for adding
        user_to_add = {
            'first_name': data.get('first_name'),
            'middle_name': data.get('middle_name'),
            'last_name': data.get('last_name'),
            'dob': dob_str,
            'age': age,
            'contact': contact_number_clean,  # Use cleaned contact number
            'address': address_string,
            'username': data.get('username'),
            'email': email,
            'password_hash': hash_password(password)
        }
        
        # 10. Add user and redirect to login
        add_user(user_to_add)
        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form_data={})

# Route for real-time duplicate checking
@auth_bp.route('/check-duplicate', methods=['POST'])
def check_duplicate():
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    
    exists = False
    if field == 'username':
        exists = bool(find_user(value))
    elif field == 'email':
        exists = bool(find_user_by_email(value))
    elif field == 'contact':
        exists = bool(find_user_by_contact(value))
    
    return jsonify({'exists': exists})

# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username').strip() if request.form.get('username') else ''
        p = request.form.get('password').strip() if request.form.get('password') else ''

        user = find_user(u)
        
        if user and verify_password(user.get('password_hash'), p):
            session.clear()
            session['user'] = user['username']
            flash('Logged in', 'success')
            return redirect(url_for('main.home'))
        
        flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

# Logout Route
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('auth.login'))

# Forgot Password Route
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = find_user(username)
        if not user:
            return jsonify({'status': 'error', 'message': 'Username not found'})
        
        # Generate OTP
        otp = '{:06d}'.format(random.randint(0, 999999))
        session['otp'] = otp
        session['otp_user'] = username
        session['otp_expires'] = (datetime.utcnow() + timedelta(minutes=3)).isoformat()
        
        return jsonify({
            'status': 'success', 
            'message': f'OTP (demo): {otp} — expires in 3 minutes'
        })
    
    return render_template('forgot_password.html')

# Verify OTP Route
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    otp = request.form.get('otp')
    newp = request.form.get('password')
    conf = request.form.get('confirm_password')

    if not (otp and newp and conf):
        return jsonify({'status': 'error', 'message': 'Please fill all fields'})
    
    if newp != conf:
        return jsonify({'status': 'error', 'message': 'Passwords do not match'})
    
    stored = session.get('otp')
    usern = session.get('otp_user')
    expires = session.get('otp_expires')

    if not stored or not usern or not expires:
        return jsonify({'status': 'error', 'message': 'Start forgot password again'})
    
    if datetime.utcnow() > datetime.fromisoformat(expires):
        session.pop('otp', None)
        session.pop('otp_expires', None)
        return jsonify({'status': 'error', 'message': 'OTP expired'})
    
    if otp != stored:
        return jsonify({'status': 'error', 'message': 'Invalid OTP'})

    # Update password
    update_user(usern, {'password_hash': hash_password(newp)})

    # Clear session data
    session.pop('otp', None)
    session.pop('otp_user', None)
    session.pop('otp_expires', None)

    return jsonify({'status': 'success', 'message': 'Password successfully updated. Please login.'})