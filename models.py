import json, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE, 'users.json')
NOTES_FILE = os.path.join(BASE, 'notes.json')

def _read(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _write(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Users
def get_users():
    return _read(USERS_FILE).get('users', [])

def save_users(users):
    _write(USERS_FILE, {'users': users})

def find_user(username):
    for u in get_users():
        if u.get('username') == username:
            return u
    return None

def add_user(u):
    users = get_users(); users.append(u); save_users(users)

def update_user(username, updates):
    users = get_users()
    for i,usr in enumerate(users):
        if usr.get('username') == username:
            users[i].update(updates)
            save_users(users)
            return users[i]
    return None

def hash_password(pw):
    return generate_password_hash(pw)

def verify_password(hashpw, pw):
    return check_password_hash(hashpw, pw)

# Notes
def get_notes():
    return _read(NOTES_FILE).get('notes', [])

def save_notes(notes):
    _write(NOTES_FILE, {'notes': notes})

def create_note(owner, title, content):
    notes = get_notes()
    nid = int(datetime.utcnow().timestamp() * 1000)
    note = {'id': nid, 'owner': owner, 'title': title, 'content': content or '', 'status': 'active', 'created_at': datetime.utcnow().isoformat(), 'updated_at': datetime.utcnow().isoformat()}
    notes.append(note); save_notes(notes); return note

def find_note(nid):
    for n in get_notes():
        if n.get('id') == nid:
            return n
    return None

def update_note(nid, updates):
    notes = get_notes()
    for i,n in enumerate(notes):
        if n.get('id') == nid:
            notes[i].update(updates); notes[i]['updated_at'] = datetime.utcnow().isoformat(); save_notes(notes); return notes[i]
    return None

def soft_delete(nid):
    return update_note(nid, {'status': 'archived'})

def restore(nid):
    return update_note(nid, {'status': 'active'})

def permanent_delete(nid):
    notes = [n for n in get_notes() if n.get('id') != nid]; save_notes(notes); return True
def find_user_by_email(email):
    """Find user by email address (case-insensitive)"""
    email_lower = email.lower()
    for u in get_users():
        if u.get('email', '').lower() == email_lower:
            return u
    return None

def find_user_by_contact(contact_number):
    """Find user by contact number"""
    for u in get_users():
        if u.get('contact') == contact_number:
            return u
    return None