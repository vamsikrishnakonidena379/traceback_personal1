"""
TrackeBack Comprehensive Flask Backend
Handles 100,000 realistic items with full API functionality
Works with SQLite database (compatible with MySQL structure)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import json
from email_verification_service import EmailVerificationService
from user_management import create_user, get_user_by_email, verify_password, update_last_login, verify_user_email, get_user_stats
from werkzeug.utils import secure_filename
import uuid
from profile_manager import create_profile_endpoints

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-2025-comprehensive'
CORS(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trackeback_100k.db')

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Save uploaded file and return the filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(filepath)
            return unique_filename
        except Exception as e:
            print(f"Error saving file: {e}")
            return None
    return None

# Initialize email verification service
verification_service = EmailVerificationService(DB_PATH)

def get_db():
    """Get database connection with row factory"""
    if not os.path.exists(DB_PATH):
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """Convert sqlite3.Row to dictionary"""
    if row is None:
        return None
    return dict(row)

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'message': 'TrackeBack Comprehensive API - 100K Items',
        'version': '3.0.0',
        'database': 'SQLite (MySQL Compatible)',
        'status': 'Running',
        'features': [
            'Real Kent State campus locations',
            '100,000 realistic lost and found items',
            'Security question verification system',
            'Privacy protection for found items',
            'Smart search and filtering',
            'Statistical analytics'
        ]
    })

# Image functionality removed - no longer serving images

@app.route('/health')
def health():
    """Health check with database statistics"""
    conn = get_db()
    if not conn:
        return jsonify({
            'status': 'error',
            'message': 'Database not found. Run generate_100k_database.py first',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    try:
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute('SELECT COUNT(*) as count FROM lost_items')
        lost_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM found_items')
        found_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM categories')
        categories_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM locations')
        locations_count = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'statistics': {
                'total_items': lost_count + found_count,
                'lost_items': lost_count,
                'found_items': found_count,
                'categories': categories_count,
                'locations': locations_count
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/categories')
def get_categories():
    """Get all categories"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        categories = conn.execute('''
            SELECT c.*, 
                   (SELECT COUNT(*) FROM lost_items WHERE category_id = c.id) as lost_count,
                   (SELECT COUNT(*) FROM found_items WHERE category_id = c.id) as found_count
            FROM categories c 
            ORDER BY c.name
        ''').fetchall()
        
        conn.close()
        
        result = []
        for cat in categories:
            cat_dict = dict_from_row(cat)
            cat_dict['total_items'] = cat_dict['lost_count'] + cat_dict['found_count']
            result.append(cat_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations')
def get_locations():
    """Get all Kent State locations"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        locations = conn.execute('''
            SELECT l.*, 
                   (SELECT COUNT(*) FROM lost_items WHERE location_id = l.id) as lost_count,
                   (SELECT COUNT(*) FROM found_items WHERE location_id = l.id) as found_count
            FROM locations l 
            ORDER BY l.name
        ''').fetchall()
        
        conn.close()
        
        result = []
        for loc in locations:
            loc_dict = dict_from_row(loc)
            loc_dict['total_items'] = loc_dict['lost_count'] + loc_dict['found_count']
            result.append(loc_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lost-items')
def get_lost_items():
    """Get lost items with pagination and filtering"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 100)), 500)  # Default 100, Max 500 items per page
        category_id = request.args.get('category_id')
        location_id = request.args.get('location_id')
        color = request.args.get('color')
        search = request.args.get('search', '').strip()
        
        # Build query
        where_conditions = ['l.is_resolved = 0']  # Only unresolved items
        params = []
        
        if category_id:
            where_conditions.append('l.category_id = ?')
            params.append(category_id)
        
        if location_id:
            where_conditions.append('l.location_id = ?')
            params.append(location_id)
        
        if color:
            where_conditions.append('LOWER(l.color) = LOWER(?)')
            params.append(color)
        
        if search:
            where_conditions.append('(LOWER(l.title) LIKE LOWER(?) OR LOWER(l.description) LIKE LOWER(?))')
            search_term = f'%{search}%'
            params.extend([search_term, search_term])
        
        where_clause = ' AND '.join(where_conditions)
        offset = (page - 1) * limit
        
        # Get total count
        count_query = f'''
            SELECT COUNT(*) as total
            FROM lost_items l
            JOIN categories c ON l.category_id = c.id
            JOIN locations loc ON l.location_id = loc.id
            WHERE {where_clause}
        '''
        
        total = conn.execute(count_query, params).fetchone()['total']
        
        # Get items
        items_query = f'''
            SELECT l.rowid as id, l.category_id, l.location_id,
                   l.title, l.description, l.color, l.size,
                   l.image_filename as image_url, l.date_lost, l.time_lost,
                   l.is_resolved, l.created_at, l.additional_details,
                   l.user_name, l.user_email, l.user_phone,
                   c.name as category_name, loc.name as location_name,
                   loc.building_code, loc.description as location_description
            FROM lost_items l
            JOIN categories c ON l.category_id = c.id
            JOIN locations loc ON l.location_id = loc.id
            WHERE {where_clause}
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
        '''
        
        params.extend([limit, offset])
        items = conn.execute(items_query, params).fetchall()
        
        conn.close()
        
        # Format response
        items_list = [dict_from_row(item) for item in items]
        
        # Format image URLs for all items
        for item in items_list:
            if item.get('image_url'):
                item['image_url'] = f"http://localhost:5000/api/uploads/{item['image_url']}"
            if 'location' in item:
                item['location_lost'] = item['location']
        
        # Debug: Print ALL items to see their image URLs
        if items_list:
            print(f"DEBUG: All lost items:")
            for i, item in enumerate(items_list):
                print(f"  {i+1}. ID {item.get('id')} - {item.get('title')} - image_url: {item.get('image_url')}")
        
        return jsonify({
            'items': items_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
                'has_next': page * limit < total,
                'has_prev': page > 1
            },
            'filters': {
                'category_id': category_id,
                'location_id': location_id,
                'color': color,
                'search': search
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/found-items')
def get_found_items():
    """
    Get found items with 30-day privacy policy
    
    Privacy Policy:
    - Items newer than 30 days are PRIVATE (only name and location shown)
    - Items older than 30 days become PUBLIC (full details visible)
    - Dashboard matching system bypasses this with include_private=true
    - show_all=true will return both private and public items for found items page
    
    This protects finder privacy while allowing the matching system to work
    and ensures old unclaimed items become publicly available.
    """
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 100)), 500)  # Default 100, Max 500 items per page
        category_id = request.args.get('category_id')
        location_id = request.args.get('location_id')
        color = request.args.get('color')
        search = request.args.get('search', '').strip()
        include_private = request.args.get('include_private', 'false').lower() == 'true'
        show_all = request.args.get('show_all', 'false').lower() == 'true'  # New parameter for found page
        
        # Calculate 30 days ago threshold
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build query - show all items if show_all=true, otherwise only public items
        where_conditions = ['f.is_claimed = 0']  # Only unclaimed items
        
        # Add 30-day privacy filter unless include_private or show_all is true
        if not include_private and not show_all:
            where_conditions.append(f"f.created_at <= '{thirty_days_ago}'")
        
        params = []
        
        if category_id:
            where_conditions.append('f.category_id = ?')
            params.append(category_id)
        
        if location_id:
            where_conditions.append('f.location_id = ?')
            params.append(location_id)
        
        if color:
            where_conditions.append('LOWER(f.color) = LOWER(?)')
            params.append(color)
        
        if search:
            where_conditions.append('(LOWER(f.title) LIKE LOWER(?) OR LOWER(f.description) LIKE LOWER(?))')
            search_term = f'%{search}%'
            params.extend([search_term, search_term])
        
        where_clause = ' AND '.join(where_conditions)
        offset = (page - 1) * limit
        
        # Get total count
        count_query = f'''
            SELECT COUNT(*) as total
            FROM found_items f
            JOIN categories c ON f.category_id = c.id
            JOIN locations loc ON f.location_id = loc.id
            WHERE {where_clause}
        '''
        
        total = conn.execute(count_query, params).fetchone()['total']
        
        # Get items
        items_query = f'''
            SELECT f.rowid as id, f.category_id, f.location_id,
                   f.title, f.description, f.color, f.size,
                   f.image_filename as image_url, f.date_found, f.time_found,
                   f.current_location, f.finder_notes, f.is_private, f.privacy_expires_at,
                   f.is_claimed, f.created_at, f.privacy_expires,
                   f.finder_name, f.finder_email, f.finder_phone,
                   c.name as category_name, loc.name as location_name,
                   loc.building_code, loc.description as location_description
            FROM found_items f
            JOIN categories c ON f.category_id = c.id
            JOIN locations loc ON f.location_id = loc.id
            WHERE {where_clause}
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
        '''
        
        params.extend([limit, offset])
        items = conn.execute(items_query, params).fetchall()
        
        conn.close()
        
        # Apply privacy filtering
        items_list = []
        for item in items:
            item_dict = dict_from_row(item)
            
            # Format image URL
            if item_dict.get('image_url'):
                item_dict['image_url'] = f"http://localhost:5000/api/uploads/{item_dict['image_url']}"
            
            # Add location_found field
            if 'location_name' in item_dict:
                item_dict['location_found'] = item_dict['location_name']
            
            # Check if item is within 30-day privacy window
            item_created_at = datetime.fromisoformat(item_dict['created_at'])
            is_within_30_days = (datetime.now() - item_created_at).days < 30
            
            # Determine if item should show private data
            if is_within_30_days and not include_private:
                # Item is private - hide everything except name and location
                item_dict['is_currently_private'] = True
                item_dict['description'] = 'Details hidden for privacy protection'
                item_dict['color'] = None
                item_dict['size'] = None
                item_dict['image_url'] = None
                item_dict['date_found'] = None
                item_dict['time_found'] = None
                item_dict['finder_name'] = 'Anonymous'
                item_dict['finder_email'] = None
                item_dict['finder_phone'] = None
                item_dict['current_location'] = 'Hidden'
                item_dict['finder_notes'] = 'Contact information available after ownership verification'
            else:
                # Item is public or include_private=true
                item_dict['is_currently_private'] = False
            
            items_list.append(item_dict)
        
        return jsonify({
            'items': items_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
                'has_next': page * limit < total,
                'has_prev': page > 1
            },
            'filters': {
                'category_id': category_id,
                'location_id': location_id,
                'color': color,
                'search': search,
                'include_private': include_private
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lost-items/<int:item_id>')
def get_lost_item(item_id):
    """Get a single lost item by ID"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        query = '''
            SELECT l.rowid as id, l.category_id, l.location_id,
                   l.title, l.description, l.color, l.size,
                   l.image_filename as image_url, l.date_lost, l.time_lost,
                   l.is_resolved, l.created_at, l.additional_details,
                   l.user_name, l.user_email, l.user_phone,
                   c.name as category, loc.name as location
            FROM lost_items l
            JOIN categories c ON l.category_id = c.id
            JOIN locations loc ON l.location_id = loc.id
            WHERE l.rowid = ?
        '''
        
        item = conn.execute(query, (item_id,)).fetchone()
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        item_dict = dict(item)
        item_dict['type'] = 'LOST'
        
        # Format image URL if exists
        if item_dict.get('image_url'):
            item_dict['image_url'] = f"http://localhost:5000/api/uploads/{item_dict['image_url']}"
        
        # Ensure location field is properly named
        if 'location' in item_dict:
            item_dict['location_lost'] = item_dict['location']
        
        return jsonify({'item': item_dict})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/found-items/<int:item_id>')
def get_found_item(item_id):
    """Get a single found item by ID"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        query = '''
            SELECT f.rowid as id, f.category_id, f.location_id,
                   f.title, f.description, f.color, f.size,
                   f.image_filename as image_url, f.date_found, f.time_found,
                   f.current_location, f.finder_notes, f.is_private, f.privacy_expires_at,
                   f.is_claimed, f.created_at, f.privacy_expires,
                   f.finder_name, f.finder_email, f.finder_phone,
                   c.name as category, loc.name as location
            FROM found_items f
            JOIN categories c ON f.category_id = c.id
            JOIN locations loc ON f.location_id = loc.id
            WHERE f.rowid = ?
        '''
        
        item = conn.execute(query, (item_id,)).fetchone()
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        item_dict = dict(item)
        item_dict['type'] = 'FOUND'
        
        # Format image URL if exists
        if item_dict.get('image_url'):
            item_dict['image_url'] = f"http://localhost:5000/api/uploads/{item_dict['image_url']}"
        
        # Ensure location field is properly named
        if 'location' in item_dict:
            item_dict['location_found'] = item_dict['location']
        
        # Apply privacy filtering for found items
        if item_dict.get('is_private') and item_dict.get('privacy_expiry'):
            from datetime import datetime
            try:
                expiry = datetime.fromisoformat(item_dict['privacy_expiry'].replace('Z', '+00:00'))
                now = datetime.now(expiry.tzinfo) if expiry.tzinfo else datetime.now()
                
                if now < expiry:
                    # Still private - hide sensitive info
                    item_dict['is_currently_private'] = True
                    item_dict['description'] = 'Private item - verify ownership to see details'
                    item_dict['finder_notes'] = 'Contact information available after ownership verification'
                else:
                    item_dict['is_currently_private'] = False
            except:
                item_dict['is_currently_private'] = False
        else:
            item_dict['is_currently_private'] = False
        
        return jsonify({'item': item_dict})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security-questions/<int:found_item_id>')
def get_security_questions(found_item_id):
    """Get security questions for ownership verification"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        # Verify item exists (use rowid, not id column)
        item = conn.execute(
            'SELECT rowid as id, title FROM found_items WHERE rowid = ? AND is_claimed = 0',
            (found_item_id,)
        ).fetchone()
        
        if not item:
            conn.close()
            return jsonify({'error': 'Item not found or already claimed'}), 404
        
        # Get questions with multiple choice options (without correct_choice)
        questions = conn.execute('''
            SELECT id, question, question_type, choice_a, choice_b, choice_c, choice_d
            FROM security_questions 
            WHERE found_item_id = ?
            ORDER BY id
        ''', (found_item_id,)).fetchall()
        
        conn.close()
        
        if not questions:
            return jsonify({'error': 'No security questions found for this item'}), 404
        
        return jsonify({
            'item': dict_from_row(item),
            'questions': [dict_from_row(q) for q in questions]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-ownership', methods=['POST'])
def verify_ownership():
    """Verify ownership through security questions"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        found_item_id = data.get('found_item_id')
        user_answers = data.get('answers', {})
        
        if not found_item_id:
            return jsonify({'error': 'Found item ID required'}), 400
        
        # Get all questions with correct answers
        questions = conn.execute('''
            SELECT id, question, correct_choice, question_type
            FROM security_questions 
            WHERE found_item_id = ?
        ''', (found_item_id,)).fetchall()
        
        if not questions:
            conn.close()
            return jsonify({'error': 'No security questions found'}), 404
        
        # Verify answers
        correct_answers = 0
        total_questions = len(questions)
        
        print(f"\n🔍 Verification Debug for item {found_item_id}:")
        print(f"Total questions: {total_questions}")
        print(f"User answers received: {user_answers}")
        
        for question in questions:
            question_id = str(question['id'])
            correct_choice = str(question['correct_choice']).strip().upper()
            
            if question_id in user_answers:
                user_answer = str(user_answers[question_id]).strip().upper()
                is_correct = user_answer == correct_choice
                
                print(f"Question {question_id}: '{question['question']}'")
                print(f"  User answered: '{user_answer}' | Correct: '{correct_choice}' | Match: {is_correct}")
                
                if is_correct:
                    correct_answers += 1
            else:
                print(f"Question {question_id}: No answer provided")
        
        print(f"Result: {correct_answers}/{total_questions} correct ({correct_answers/total_questions*100:.1f}%)")
        print("=" * 70 + "\n")
        
        # Calculate success rate (need at least 67% correct)
        success_rate = correct_answers / total_questions
        verification_successful = success_rate >= 0.67
        
        if verification_successful:
            # Get complete item details with finder information (use rowid, not id)
            # Join with users table to get finder's user_id
            item_details = conn.execute('''
                SELECT f.rowid as id, f.*, c.name as category_name, loc.name as location_name,
                       loc.building_code, loc.description as location_description,
                       u.id as finder_user_id
                FROM found_items f
                JOIN categories c ON f.category_id = c.id
                JOIN locations loc ON f.location_id = loc.id
                LEFT JOIN users u ON f.finder_email = u.email
                WHERE f.rowid = ?
            ''', (found_item_id,)).fetchone()
            
            if not item_details:
                conn.close()
                return jsonify({'error': 'Item not found'}), 404
            
            item_dict = dict_from_row(item_details)
            
            # Get claimer info from request (current user)
            claimer_user_id = data.get('claimer_user_id')
            claimer_name = data.get('claimer_name', 'Unknown')
            claimer_email = data.get('claimer_email', '')
            claimer_phone = data.get('claimer_phone', '')
            
            # Create ownership claim record
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ownership_claims (
                    item_id, item_type, item_title,
                    claimer_user_id, claimer_name, claimer_email, claimer_phone,
                    finder_name, finder_email, finder_phone,
                    claimed_status
                ) VALUES (?, 'FOUND', ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
            ''', (
                found_item_id, 
                item_dict['title'],
                claimer_user_id,
                claimer_name,
                claimer_email,
                claimer_phone,
                item_dict['finder_name'],
                item_dict['finder_email'],
                item_dict['finder_phone']
            ))
            
            claim_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ Claim record created: ID {claim_id} for item {found_item_id}")
            
            return jsonify({
                'verified': True,
                'claim_id': claim_id,
                'message': f'Verification successful! You answered {correct_answers}/{total_questions} questions correctly.',
                'success_rate': round(success_rate * 100, 1),
                'finder_details': {
                    'user_id': item_dict.get('finder_user_id'),
                    'name': item_dict['finder_name'],
                    'email': item_dict['finder_email'],
                    'phone': item_dict['finder_phone']
                },
                'item_details': {
                    'title': item_dict['title'],
                    'description': item_dict['description'],
                    'category': item_dict['category_name'],
                    'location_found': item_dict['location_name'],
                    'date_found': item_dict['date_found'],
                    'current_location': item_dict['current_location'],
                    'finder_notes': item_dict['finder_notes']
                }
            })
        else:
            conn.close()
            required_correct = max(1, int(total_questions * 0.67))
            
            return jsonify({
                'verified': False,
                'message': f'Verification failed. You answered {correct_answers}/{total_questions} questions correctly. You need at least {required_correct}/{total_questions} correct answers.',
                'success_rate': round(success_rate * 100, 1),
                'attempts_remaining': 2  # Could implement attempt tracking
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security-questions/bulk', methods=['POST'])
def create_security_questions_bulk():
    """Create multiple security questions for a found item"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        found_item_id = data.get('found_item_id')
        questions = data.get('questions', [])
        
        if not found_item_id:
            return jsonify({'error': 'Found item ID required'}), 400
        
        if not questions or len(questions) < 2:
            return jsonify({'error': 'At least 2 security questions required'}), 400
        
        if len(questions) > 5:
            return jsonify({'error': 'Maximum 5 security questions allowed'}), 400
        
        # Verify the found item exists and hasn't been claimed (use rowid, not id)
        item = conn.execute(
            'SELECT rowid as id FROM found_items WHERE rowid = ? AND is_claimed = 0',
            (found_item_id,)
        ).fetchone()
        
        if not item:
            conn.close()
            return jsonify({'error': 'Found item not found or already claimed'}), 404
        
        # Delete any existing questions for this item (in case of re-submission)
        conn.execute('DELETE FROM security_questions WHERE found_item_id = ?', (found_item_id,))
        
        # Insert all questions
        created_questions = []
        for q in questions:
            if not q.get('question') or not q.get('choice_a') or not q.get('choice_b'):
                conn.close()
                return jsonify({'error': 'Each question must have a question text and at least 2 choices (A and B)'}), 400
            
            if q.get('correct_choice') not in ['A', 'B', 'C', 'D']:
                conn.close()
                return jsonify({'error': 'Correct choice must be A, B, C, or D'}), 400
            
            # Get the answer value based on the correct choice
            choice_map = {
                'A': q.get('choice_a'),
                'B': q.get('choice_b'),
                'C': q.get('choice_c'),
                'D': q.get('choice_d')
            }
            answer_value = choice_map.get(q['correct_choice'])
            
            cursor = conn.execute('''
                INSERT INTO security_questions 
                (found_item_id, question, answer, choice_a, choice_b, choice_c, choice_d, correct_choice, question_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (
                found_item_id,
                q['question'],
                answer_value,  # Add the answer field for backward compatibility
                q['choice_a'],
                q['choice_b'],
                q.get('choice_c'),
                q.get('choice_d'),
                q['correct_choice'],
                q.get('question_type', 'multiple_choice')
            ))
            
            created_questions.append({
                'id': cursor.lastrowid,
                'question': q['question']
            })
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{len(created_questions)} security questions created successfully',
            'questions': created_questions,
            'found_item_id': found_item_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search_items():
    """Universal search across lost and found items"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        query = request.args.get('q', '').strip()
        item_type = request.args.get('type', 'all')  # 'lost', 'found', 'all'
        limit = min(int(request.args.get('limit', 100)), 500)  # Default 100, Max 500 items per page
        
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        results = {'lost_items': [], 'found_items': [], 'total': 0}
        search_term = f'%{query}%'
        
        if item_type in ['lost', 'all']:
            lost_items = conn.execute('''
                SELECT l.*, c.name as category_name, loc.name as location_name
                FROM lost_items l
                JOIN categories c ON l.category_id = c.id
                JOIN locations loc ON l.location_id = loc.id
                WHERE l.is_resolved = 0 
                AND (LOWER(l.title) LIKE LOWER(?) OR LOWER(l.description) LIKE LOWER(?) 
                     OR LOWER(c.name) LIKE LOWER(?) OR LOWER(loc.name) LIKE LOWER(?))
                ORDER BY l.created_at DESC
                LIMIT ?
            ''', (search_term, search_term, search_term, search_term, limit)).fetchall()
            
            results['lost_items'] = [dict_from_row(item) for item in lost_items]
        
        if item_type in ['found', 'all']:
            found_items = conn.execute('''
                SELECT f.*, c.name as category_name, loc.name as location_name
                FROM found_items f
                JOIN categories c ON f.category_id = c.id
                JOIN locations loc ON f.location_id = loc.id
                WHERE f.is_claimed = 0
                AND (LOWER(f.title) LIKE LOWER(?) OR LOWER(f.description) LIKE LOWER(?) 
                     OR LOWER(c.name) LIKE LOWER(?) OR LOWER(loc.name) LIKE LOWER(?))
                ORDER BY f.created_at DESC
                LIMIT ?
            ''', (search_term, search_term, search_term, search_term, limit)).fetchall()
            
            # Apply privacy filtering to found items
            filtered_found = []
            for item in found_items:
                item_dict = dict_from_row(item)
                
                if item_dict.get('is_private'):
                    if item_dict.get('privacy_expires_at'):
                        expires_at = datetime.fromisoformat(item_dict['privacy_expires_at'].replace('Z', '+00:00'))
                        if datetime.now() < expires_at.replace(tzinfo=None):
                            item_dict['description'] = 'Details hidden - verify ownership to view'
                            item_dict['finder_name'] = 'Anonymous'
                
                filtered_found.append(item_dict)
            
            results['found_items'] = filtered_found
        
        results['total'] = len(results['lost_items']) + len(results['found_items'])
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get comprehensive system statistics"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        stats = {}
        
        # Basic counts
        stats['active_lost_items'] = conn.execute(
            'SELECT COUNT(*) as count FROM lost_items WHERE is_resolved = 0'
        ).fetchone()['count']
        
        stats['unclaimed_found_items'] = conn.execute(
            'SELECT COUNT(*) as count FROM found_items WHERE is_claimed = 0'
        ).fetchone()['count']
        
        stats['items_claimed'] = conn.execute(
            'SELECT COUNT(*) as count FROM found_items WHERE is_claimed = 1'
        ).fetchone()['count']
        
        stats['total_categories'] = conn.execute(
            'SELECT COUNT(*) as count FROM categories'
        ).fetchone()['count']
        
        stats['total_locations'] = conn.execute(
            'SELECT COUNT(*) as count FROM locations'
        ).fetchone()['count']
        
        # Recent activity (last 7 days)
        stats['recent_lost_items'] = conn.execute(
            "SELECT COUNT(*) as count FROM lost_items WHERE date(created_at) >= date('now', '-7 days')"
        ).fetchone()['count']
        
        stats['recent_found_items'] = conn.execute(
            "SELECT COUNT(*) as count FROM found_items WHERE date(created_at) >= date('now', '-7 days')"
        ).fetchone()['count']
        
        # Privacy statistics
        stats['private_found_items'] = conn.execute(
            "SELECT COUNT(*) as count FROM found_items WHERE is_private = 1 AND datetime(privacy_expires_at) > datetime('now')"
        ).fetchone()['count']
        
        # Category breakdown
        category_stats = conn.execute('''
            SELECT c.name, 
                   COUNT(CASE WHEN l.id IS NOT NULL THEN 1 END) as lost_count,
                   COUNT(CASE WHEN f.id IS NOT NULL THEN 1 END) as found_count
            FROM categories c
            LEFT JOIN lost_items l ON c.id = l.category_id AND l.is_resolved = 0
            LEFT JOIN found_items f ON c.id = f.category_id AND f.is_claimed = 0
            GROUP BY c.id, c.name
            ORDER BY (COUNT(CASE WHEN l.id IS NOT NULL THEN 1 END) + COUNT(CASE WHEN f.id IS NOT NULL THEN 1 END)) DESC
            LIMIT 5
        ''').fetchall()
        
        stats['top_categories'] = [dict_from_row(cat) for cat in category_stats]
        
        # Location breakdown
        location_stats = conn.execute('''
            SELECT loc.name, loc.building_code,
                   COUNT(CASE WHEN l.id IS NOT NULL THEN 1 END) as lost_count,
                   COUNT(CASE WHEN f.id IS NOT NULL THEN 1 END) as found_count
            FROM locations loc
            LEFT JOIN lost_items l ON loc.id = l.location_id AND l.is_resolved = 0
            LEFT JOIN found_items f ON loc.id = f.location_id AND f.is_claimed = 0
            GROUP BY loc.id, loc.name, loc.building_code
            ORDER BY (COUNT(CASE WHEN l.id IS NOT NULL THEN 1 END) + COUNT(CASE WHEN f.id IS NOT NULL THEN 1 END)) DESC
            LIMIT 5
        ''').fetchall()
        
        stats['top_locations'] = [dict_from_row(loc) for loc in location_stats]
        
        # Calculate totals
        stats['total_items'] = stats['active_lost_items'] + stats['unclaimed_found_items']
        stats['recent_total'] = stats['recent_lost_items'] + stats['recent_found_items']
        
        conn.close()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login with database verification"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    print(f"🔍 Login attempt: email='{email}'")
    print(f"📝 Raw data received: {data}")
    print(f"🔑 Password received: '{password}' (length: {len(password)})")
    
    if not email or not password:
        print("❌ Login failed: Email and password required")
        return jsonify({'error': 'Email and password are required'}), 400
    
    if not email.endswith('@kent.edu'):
        print("❌ Login failed: Not @kent.edu email")
        return jsonify({'error': 'Only Kent State (@kent.edu) email addresses are allowed'}), 400
    
    # Get user from database
    user = get_user_by_email(email)
    
    if not user:
        print("❌ Login failed: User not found")
        return jsonify({'error': 'Email not found. Please sign up first.'}), 401
    
    print(f"👤 User found: {user['full_name']}")
    print(f"🔑 Expected hash: {user['password_hash']}")
    
    # Test password verification with detailed logging
    password_valid = verify_password(password, user['password_hash'])
    print(f"🔓 Password verification result: {password_valid}")
    
    if not password_valid:
        print("❌ Login failed: Invalid password")
        # Additional debug info
        import hashlib
        test_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"🔨 Generated hash for received password: {test_hash}")
        print(f"🔧 Hashes match: {test_hash == user['password_hash']}")
        return jsonify({'error': 'Invalid credentials. Please check your password.'}), 401
    
    # Check if user is active
    if not user.get('is_active', True):
        print("❌ Login failed: Account deactivated")
        return jsonify({'error': 'Account is deactivated'}), 401
    
    # Update last login
    update_last_login(email)
    
    print(f"✅ Login successful: {user['full_name']}")
    
    return jsonify({
        'message': 'Login successful',
        'session_token': f'demo-token-{user["id"]}-2025',  # In real app, use JWT
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['full_name'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'verified': user['is_verified'],
            'profile_completed': user.get('profile_completed', 0),
            'created_at': user['created_at']
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user with database storage"""
    data = request.get_json()
    
    # Debug: Print received data
    print(f"🔍 Register endpoint received data: {data}")
    
    email = data.get('email', '').strip().lower() if data.get('email') else ''
    password = data.get('password', '').strip() if data.get('password') else ''
    
    # Handle both name formats: single 'name' field or separate 'first_name'/'last_name'
    first_name = ''
    last_name = ''
    
    if data.get('name'):
        # Split single name into first and last
        name_parts = data.get('name', '').strip().split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
    elif data.get('first_name') or data.get('last_name'):
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
    
    full_name = f"{first_name} {last_name}".strip()
    
    print(f"📧 Email: '{email}'")
    print(f"🔑 Password: {'*' * len(password) if password else 'EMPTY'}")
    print(f"👤 Name: '{full_name}' (first: '{first_name}', last: '{last_name}')")
    
    # Validation
    if not email:
        print("❌ Validation failed: Email is required")
        return jsonify({'error': 'Email is required'}), 400
    
    if not email.endswith('@kent.edu'):
        print("❌ Validation failed: Not @kent.edu email")
        return jsonify({'error': 'Only Kent State (@kent.edu) email addresses are allowed'}), 400
    
    if not password:
        print("❌ Validation failed: Password is required")
        return jsonify({'error': 'Password is required'}), 400
    
    if not first_name:
        print(f"❌ Validation failed: First name is required")
        return jsonify({'error': 'First name is required'}), 400
    
    if not last_name:
        print(f"❌ Validation failed: Last name is required")
        return jsonify({'error': 'Last name is required'}), 400
    
    print("✅ All validations passed!")
    
    # Create user in database
    success, result = create_user(email, password, first_name, last_name)
    
    if success:
        print(f"✅ User created in database: {result}")
        
        # Send verification email
        verification_success, verification_message = verification_service.send_verification_email(
            email, "Account Registration", "registration", result['id']
        )
        
        if verification_success:
            print(f"✅ Verification email sent: {verification_message}")
        else:
            print(f"⚠️ User created but email failed: {verification_message}")
        
        return jsonify({
            'message': 'Registration successful! Please check your email for verification code.',
            'user': {
                'id': result['id'],
                'email': result['email'],
                'name': result['name'],
                'first_name': result['first_name'],
                'last_name': result['last_name'],
                'verified': result['is_verified']
            },
            'requires_verification': True
        }), 201
    else:
        print(f"❌ User creation failed: {result}")
        return jsonify({'error': result}), 400

@app.route('/api/auth/resend', methods=['POST'])
def auth_resend():
    """Resend verification code (auth context)"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    if not email.endswith('@kent.edu'):
        return jsonify({'error': 'Only Kent State (@kent.edu) email addresses are allowed'}), 400
    
    # Clear old codes for this email
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM email_verifications WHERE email = ? AND is_verified = FALSE", (email,))
    conn.commit()
    conn.close()
    
    success, message = verification_service.send_verification_email(
        email, "Account Verification", "registration", None
    )
    
    if success:
        return jsonify({'message': f'New verification code sent to {email}'}), 200
    else:
        return jsonify({'error': message}), 400

@app.route('/api/auth/verify', methods=['POST'])
def auth_verify():
    """Verify email code (auth context)"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    
    print(f"🔍 Auth verify endpoint received: email='{email}', code='{code}'")
    
    if not email or not code:
        print("❌ Validation failed: Email and code are required")
        return jsonify({'error': 'Email and code are required'}), 400
    
    if not email.endswith('@kent.edu'):
        print("❌ Validation failed: Not @kent.edu email")
        return jsonify({'error': 'Only Kent State (@kent.edu) email addresses are allowed'}), 400
    
    success, message = verification_service.verify_code(email, code)
    
    if success:
        # Mark user as verified in database
        verify_user_email(email)
        print("✅ Email verification successful!")
        
        # Get full user data
        user = get_user_by_email(email)
        if user:
            return jsonify({
                'message': message, 
                'verified': True,
                'session_token': f'demo-token-{user["id"]}-2025',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['full_name'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'verified': True,
                    'profile_completed': user.get('profile_completed', 0),
                    'created_at': user['created_at']
                }
            }), 200
        else:
            return jsonify({
                'message': message, 
                'verified': True,
                'user': {'email': email, 'verified': True, 'profile_completed': 0}
            }), 200
    else:
        print(f"❌ Email verification failed: {message}")
        return jsonify({'error': message, 'verified': False}), 400

# Email Verification Routes
@app.route('/api/send-verification', methods=['POST'])
def send_verification():
    """Send verification code to Kent State email"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    item_title = data.get('item_title', 'TrackeBack Item')
    item_type = data.get('item_type', 'item')
    item_id = data.get('item_id')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    success, message = verification_service.send_verification_email(
        email, item_title, item_type, item_id
    )
    
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400

@app.route('/api/verify-email', methods=['POST'])
def verify_email():
    """Verify email with code"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    
    if not email or not code:
        return jsonify({'error': 'Email and code are required'}), 400
    
    success, message = verification_service.verify_code(email, code)
    
    if success:
        return jsonify({'message': message, 'verified': True}), 200
    else:
        return jsonify({'error': message, 'verified': False}), 400

@app.route('/api/check-verification/<email>')
def check_verification(email):
    """Check if email is already verified"""
    is_verified = verification_service.is_email_verified(email)
    return jsonify({'verified': is_verified})

@app.route('/api/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification code"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Clear old codes for this email
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM email_verifications WHERE email = ? AND is_verified = FALSE", (email,))
    conn.commit()
    conn.close()
    
    success, message = verification_service.send_verification_email(email)
    
    if success:
        return jsonify({'message': f'New verification code sent to {email}'}), 200
    else:
        return jsonify({'error': message}), 400

@app.route('/api/report-lost', methods=['POST'])
def report_lost_item():
    """Submit a new lost item report with optional image upload"""
    try:
        # Handle both JSON and FormData
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            image_file = None
        else:
            # FormData (with potential file upload)
            data = request.form.to_dict()
            image_file = request.files.get('image')
        
        print(f"📝 Lost item report received: {data.get('title', 'Unknown')}")
        
        # Validate required fields
        required_fields = ['title', 'description', 'category_id', 'location_id', 'date_lost', 'user_name', 'user_email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Handle file upload
        image_filename = None
        if image_file:
            print(f"📸 Processing image upload: {image_file.filename}")
            image_filename = save_uploaded_file(image_file)
            if image_filename:
                print(f"✅ Image saved: {image_filename}")
            else:
                print(f"❌ Failed to save image: {image_file.filename}")
                return jsonify({'error': 'Failed to save uploaded image'}), 400
        
        # Handle custom category/location
        category_id = data.get('category_id')
        location_id = data.get('location_id')
        
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database not available'}), 500
        
        # If category is "other", create new category
        if str(category_id).lower() == 'other':
            custom_category = data.get('custom_category', '').strip()
            if not custom_category:
                return jsonify({'error': 'Custom category is required when "Other" is selected'}), 400
            
            # Check if category already exists
            existing = conn.execute('SELECT id FROM categories WHERE LOWER(name) = LOWER(?)', (custom_category,)).fetchone()
            if existing:
                category_id = existing[0]
            else:
                # Create new category
                cursor = conn.execute(
                    'INSERT INTO categories (name, description, created_at) VALUES (?, ?, datetime("now"))',
                    (custom_category, f'Custom category: {custom_category}')
                )
                category_id = cursor.lastrowid
                print(f"🆕 Created new category: {custom_category} (ID: {category_id})")
        
        # If location is "other", create new location
        if str(location_id).lower() == 'other':
            custom_location = data.get('custom_location', '').strip()
            if not custom_location:
                return jsonify({'error': 'Custom location is required when "Other" is selected'}), 400
            
            # Check if location already exists
            existing = conn.execute('SELECT id FROM locations WHERE LOWER(name) = LOWER(?)', (custom_location,)).fetchone()
            if existing:
                location_id = existing[0]
            else:
                # Create new location
                cursor = conn.execute(
                    'INSERT INTO locations (name, code, description, created_at) VALUES (?, ?, ?, datetime("now"))',
                    (custom_location, custom_location[:4].upper(), f'Custom location: {custom_location}')
                )
                location_id = cursor.lastrowid
                print(f"🆕 Created new location: {custom_location} (ID: {location_id})")
        
        # Insert lost item
        cursor = conn.execute('''
            INSERT INTO lost_items (
                title, description, category_id, location_id, color, size,
                date_lost, time_lost, user_name, user_email, user_phone,
                additional_details, image_filename, is_resolved, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, datetime("now"))
        ''', (
            data.get('title'),
            data.get('description'),
            category_id,
            location_id,
            data.get('color', ''),
            data.get('size', ''),
            data.get('date_lost'),
            data.get('time_lost', ''),
            data.get('user_name'),
            data.get('user_email'),
            data.get('user_phone', ''),
            data.get('additional_details', ''),
            image_filename
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Lost item created with ID: {item_id}")
        
        return jsonify({
            'message': 'Lost item reported successfully',
            'item_id': item_id,
            'image_uploaded': image_filename is not None
        }), 201
        
    except Exception as e:
        print(f"❌ Error reporting lost item: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/report-found', methods=['POST'])
def report_found_item():
    """Submit a new found item report with optional image upload"""
    try:
        # Handle both JSON and FormData
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            image_file = None
        else:
            # FormData (with potential file upload)
            data = request.form.to_dict()
            image_file = request.files.get('image')
        
        print(f"📝 Found item report received: {data.get('title', 'Unknown')}")
        
        # Validate required fields
        required_fields = ['title', 'description', 'category_id', 'location_id', 'date_found', 'user_name', 'user_email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Handle file upload
        image_filename = None
        if image_file:
            print(f"📸 Processing image upload: {image_file.filename}")
            image_filename = save_uploaded_file(image_file)
            if image_filename:
                print(f"✅ Image saved: {image_filename}")
            else:
                print(f"❌ Failed to save image: {image_file.filename}")
                return jsonify({'error': 'Failed to save uploaded image'}), 400
        
        # Handle custom category/location
        category_id = data.get('category_id')
        location_id = data.get('location_id')
        
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database not available'}), 500
        
        # If category is "other", create new category
        if str(category_id).lower() == 'other':
            custom_category = data.get('custom_category', '').strip()
            if not custom_category:
                return jsonify({'error': 'Custom category is required when "Other" is selected'}), 400
            
            # Check if category already exists
            existing = conn.execute('SELECT id FROM categories WHERE LOWER(name) = LOWER(?)', (custom_category,)).fetchone()
            if existing:
                category_id = existing[0]
            else:
                # Create new category
                cursor = conn.execute(
                    'INSERT INTO categories (name, description, created_at) VALUES (?, ?, datetime("now"))',
                    (custom_category, f'Custom category: {custom_category}')
                )
                category_id = cursor.lastrowid
                print(f"🆕 Created new category: {custom_category} (ID: {category_id})")
        
        # If location is "other", create new location
        if str(location_id).lower() == 'other':
            custom_location = data.get('custom_location', '').strip()
            if not custom_location:
                return jsonify({'error': 'Custom location is required when "Other" is selected'}), 400
            
            # Check if location already exists
            existing = conn.execute('SELECT id FROM locations WHERE LOWER(name) = LOWER(?)', (custom_location,)).fetchone()
            if existing:
                location_id = existing[0]
            else:
                # Create new location
                cursor = conn.execute(
                    'INSERT INTO locations (name, code, description, created_at) VALUES (?, ?, ?, datetime("now"))',
                    (custom_location, custom_location[:4].upper(), f'Custom location: {custom_location}')
                )
                location_id = cursor.lastrowid
                print(f"🆕 Created new location: {custom_location} (ID: {location_id})")
        
        # Calculate privacy expiry (30 days from now)
        privacy_expiry = datetime.now() + timedelta(days=30)
        privacy_expiry_str = privacy_expiry.strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert found item
        cursor = conn.execute('''
            INSERT INTO found_items (
                title, description, category_id, location_id, color, size,
                date_found, time_found, finder_name, finder_email, finder_phone,
                finder_notes, current_location, is_private, privacy_expires_at,
                image_filename, is_claimed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0, datetime("now"))
        ''', (
            data.get('title'),
            data.get('description'),
            category_id,
            location_id,
            data.get('color', ''),
            data.get('size', ''),
            data.get('date_found'),
            data.get('time_found', ''),
            data.get('user_name'),  # Using user_name as finder_name
            data.get('user_email'),  # Using user_email as finder_email
            data.get('user_phone', ''),  # Using user_phone as finder_phone
            data.get('additional_details', ''),  # Using additional_details as finder_notes
            'Front Desk',  # Default current_location
            privacy_expiry_str,
            image_filename
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Found item created with ID: {item_id}")
        
        return jsonify({
            'message': 'Found item reported successfully',
            'item_id': item_id,
            'image_uploaded': image_filename is not None,
            'privacy_expires': privacy_expiry_str
        }), 201
        
    except Exception as e:
        print(f"❌ Error reporting found item: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

# ============================================
# REVIEWS ENDPOINTS
# ============================================

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """Get all approved reviews"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.row_factory = sqlite3.Row
        
        # Get only approved reviews, ordered by most recent first
        cursor = conn.execute('''
            SELECT id, user_name, user_email, rating, review_text, 
                   item_found, image_filename, created_at
            FROM reviews
            WHERE is_approved = 1
            ORDER BY created_at DESC
        ''')
        
        reviews = []
        for row in cursor.fetchall():
            review = dict(row)
            # Format image URL if exists
            if review.get('image_filename'):
                review['image_url'] = f"http://localhost:5000/api/uploads/{review['image_filename']}"
            else:
                review['image_url'] = None
            reviews.append(review)
        
        conn.close()
        
        return jsonify({
            'reviews': reviews,
            'total': len(reviews)
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching reviews: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews', methods=['POST'])
def create_review():
    """Submit a new review"""
    try:
        # Check if multipart/form-data (with potential image)
        if 'multipart/form-data' in request.content_type:
            user_name = request.form.get('user_name')
            user_email = request.form.get('user_email')
            rating = request.form.get('rating')
            review_text = request.form.get('review_text')
            item_found = request.form.get('item_found')
            image = request.files.get('image')
        else:
            # JSON request
            data = request.get_json()
            user_name = data.get('user_name')
            user_email = data.get('user_email')
            rating = data.get('rating')
            review_text = data.get('review_text')
            item_found = data.get('item_found')
            image = None
        
        # Validation
        if not all([user_name, user_email, rating, review_text]):
            return jsonify({'error': 'Missing required fields: user_name, user_email, rating, review_text'}), 400
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        except ValueError:
            return jsonify({'error': 'Rating must be a number'}), 400
        
        # Handle image upload
        image_filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            unique_filename = f"{uuid.uuid4().hex}_review_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image.save(filepath)
            image_filename = unique_filename
            print(f"✅ Review image uploaded: {image_filename}")
        
        # Insert review into database
        conn = sqlite3.connect(DB_PATH, timeout=20)
        conn.execute('PRAGMA journal_mode=WAL')
        
        cursor = conn.execute('''
            INSERT INTO reviews (user_name, user_email, rating, review_text, item_found, image_filename, is_approved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_name, user_email, rating, review_text, item_found, image_filename, 1))
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Review created with ID: {review_id}")
        
        return jsonify({
            'message': 'Review submitted successfully',
            'review_id': review_id,
            'image_uploaded': image_filename is not None
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating review: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """Get a specific review by ID"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('''
            SELECT id, user_name, user_email, rating, review_text, 
                   item_found, image_filename, created_at, is_approved
            FROM reviews
            WHERE id = ?
        ''', (review_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Review not found'}), 404
        
        review = dict(row)
        # Format image URL if exists
        if review.get('image_filename'):
            review['image_url'] = f"http://localhost:5000/api/uploads/{review['image_filename']}"
        else:
            review['image_url'] = None
        
        return jsonify(review), 200
        
    except Exception as e:
        print(f"❌ Error fetching review: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================
# ABUSE REPORTS API ENDPOINTS
# ============================================

def is_admin(user_email):
    """Check if user is an admin (aksh@kent.edu or achapala@kent.edu)"""
    if not user_email:
        return False
    email_lower = user_email.lower()
    return email_lower in ['aksh@kent.edu', 'achapala@kent.edu']


# ============================================
# OWNERSHIP CLAIMS API ENDPOINTS
# ============================================

@app.route('/api/claims', methods=['GET'])
def get_claims():
    """Get ownership claims for a user"""
    try:
        user_email = request.args.get('user_email')
        user_type = request.args.get('type', 'claimer')  # 'claimer' or 'finder'
        
        if not user_email:
            return jsonify({'error': 'User email required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_type == 'claimer':
            # Get claims where this user verified ownership
            # Join with users table to get finder_id
            cursor.execute("""
                SELECT oc.*, u.id as finder_id
                FROM ownership_claims oc
                LEFT JOIN users u ON oc.finder_email = u.email
                WHERE oc.claimer_email = ?
                ORDER BY oc.verification_date DESC
            """, (user_email,))
        else:
            # Get claims where this user is the finder
            # claimer_user_id is already in the table, but rename it to claimer_id for consistency
            cursor.execute("""
                SELECT *, claimer_user_id as claimer_id
                FROM ownership_claims 
                WHERE finder_email = ?
                ORDER BY verification_date DESC
            """, (user_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        claims = [dict(row) for row in rows]
        
        print(f"✅ Retrieved {len(claims)} claims for {user_email} (type: {user_type})")
        return jsonify({'claims': claims}), 200
        
    except Exception as e:
        print(f"❌ Error fetching claims: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/claims/<int:claim_id>', methods=['PUT'])
def update_claim(claim_id):
    """Update a claim status"""
    try:
        data = request.get_json()
        new_status = data.get('claimed_status', 'PENDING')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the item_id for this claim
        cursor.execute("SELECT item_id, item_type FROM ownership_claims WHERE claim_id = ?", (claim_id,))
        claim_info = cursor.fetchone()
        
        if not claim_info:
            conn.close()
            return jsonify({'error': 'Claim not found'}), 404
        
        item_id, item_type = claim_info
        
        # Update claim status
        cursor.execute("""
            UPDATE ownership_claims 
            SET claimed_status = ?,
                claimed_date = CASE WHEN ? = 'CLAIMED' THEN CURRENT_TIMESTAMP ELSE claimed_date END,
                notes = ?
            WHERE claim_id = ?
        """, (
            new_status,
            new_status,
            data.get('notes', ''),
            claim_id
        ))
        
        # If marking as CLAIMED, update the item's is_claimed field
        if new_status == 'CLAIMED' and item_type == 'FOUND':
            cursor.execute("""
                UPDATE found_items 
                SET is_claimed = 1
                WHERE rowid = ?
            """, (item_id,))
            print(f"✅ Marked found_item {item_id} as claimed")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Claim {claim_id} updated to {new_status}")
        return jsonify({
            'success': True,
            'message': 'Claim updated successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating claim: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports', methods=['POST'])
def create_abuse_report():
    """Create a new abuse report"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'target_id', 'category', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get current user info (should come from session/auth in production)
        reported_by_id = data.get('reported_by_id')
        reported_by_name = data.get('reported_by_name', 'Anonymous')
        reported_by_email = data.get('reported_by_email')
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Insert report
        cursor.execute("""
            INSERT INTO abuse_reports (
                type, target_id, target_title, 
                reported_by_id, reported_by_name, reported_by_email,
                category, reason, description, status, priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 'MEDIUM')
        """, (
            data['type'].upper(),
            data['target_id'],
            data.get('target_title', 'Unknown'),
            reported_by_id,
            reported_by_name,
            reported_by_email,
            data['category'],
            data['reason'],
            data.get('description', '')
        ))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Report {report_id} created successfully")
        return jsonify({
            'success': True,
            'report_id': report_id,
            'message': 'Report submitted successfully'
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating report: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports', methods=['GET'])
def get_abuse_reports():
    """Get all abuse reports (admin only)"""
    try:
        # Get query parameters
        status = request.args.get('status')
        admin_email = request.args.get('admin_email')
        
        # Check admin access
        if not is_admin(admin_email):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM abuse_reports"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status.upper())
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        reports = []
        for row in rows:
            report = dict(row)
            reports.append(report)
        
        print(f"✅ Retrieved {len(reports)} reports")
        return jsonify({'reports': reports}), 200
        
    except Exception as e:
        print(f"❌ Error fetching reports: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<int:report_id>', methods=['PUT'])
def update_abuse_report(report_id):
    """Update an abuse report (admin only)"""
    try:
        data = request.get_json()
        admin_email = data.get('admin_email')
        
        # Check admin access
        if not is_admin(admin_email):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update report
        cursor.execute("""
            UPDATE abuse_reports 
            SET status = ?, 
                moderator_notes = ?,
                moderator_action = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE report_id = ?
        """, (
            data.get('status', 'REVIEWED'),
            data.get('moderator_notes', ''),
            data.get('moderator_action', ''),
            report_id
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Report {report_id} updated successfully")
        return jsonify({
            'success': True,
            'message': 'Report updated successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating report: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<int:report_id>/delete-content', methods=['DELETE'])
def delete_reported_content(report_id):
    """Delete the content that was reported (admin only)"""
    try:
        data = request.get_json()
        admin_email = data.get('admin_email')
        
        # Check admin access
        if not is_admin(admin_email):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get report details
        cursor.execute("SELECT * FROM abuse_reports WHERE report_id = ?", (report_id,))
        report = cursor.fetchone()
        
        if not report:
            conn.close()
            return jsonify({'error': 'Report not found'}), 404
        
        report_dict = dict(report)
        target_type = report_dict['type']
        target_id = report_dict['target_id']
        
        # Delete the reported content
        if target_type == 'ITEM':
            # Try to delete from both tables (lost and found)
            cursor.execute("DELETE FROM lost_items WHERE rowid = ?", (target_id,))
            deleted_lost = cursor.rowcount
            
            cursor.execute("DELETE FROM found_items WHERE rowid = ?", (target_id,))
            deleted_found = cursor.rowcount
            
            if deleted_lost == 0 and deleted_found == 0:
                conn.close()
                return jsonify({'error': 'Item not found'}), 404
            
            print(f"✅ Deleted item {target_id} (lost: {deleted_lost}, found: {deleted_found})")
            
        elif target_type == 'USER':
            cursor.execute("DELETE FROM users WHERE rowid = ?", (target_id,))
            if cursor.rowcount == 0:
                conn.close()
                return jsonify({'error': 'User not found'}), 404
            print(f"✅ Deleted user {target_id}")
        
        # Update report status
        cursor.execute("""
            UPDATE abuse_reports 
            SET status = 'RESOLVED',
                moderator_action = 'remove_content',
                moderator_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE report_id = ?
        """, (
            data.get('moderator_notes', 'Content removed by admin'),
            report_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{target_type} deleted successfully',
            'deleted_type': target_type,
            'deleted_id': target_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error deleting content: {e}")
        return jsonify({'error': str(e)}), 500


# MESSAGING ENDPOINTS
@app.route('/api/messages/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for a user"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get unique conversations with last message
        cursor.execute('''
            SELECT 
                m1.conversation_id,
                m1.item_id,
                m1.item_type,
                m1.item_title,
                CASE 
                    WHEN m1.sender_id = ? THEN m1.receiver_id
                    ELSE m1.sender_id
                END as other_user_id,
                CASE 
                    WHEN m1.sender_id = ? THEN m1.receiver_name
                    ELSE m1.sender_name
                END as other_user_name,
                CASE 
                    WHEN m1.sender_id = ? THEN m1.receiver_email
                    ELSE m1.sender_email
                END as other_user_email,
                m1.message_text as last_message,
                m1.created_at as last_message_time,
                SUM(CASE WHEN m1.receiver_id = ? AND m1.is_read = 0 THEN 1 ELSE 0 END) as unread_count
            FROM messages m1
            INNER JOIN (
                SELECT conversation_id, MAX(created_at) as max_time
                FROM messages
                WHERE sender_id = ? OR receiver_id = ?
                GROUP BY conversation_id
            ) m2 ON m1.conversation_id = m2.conversation_id AND m1.created_at = m2.max_time
            WHERE m1.sender_id = ? OR m1.receiver_id = ?
            GROUP BY m1.conversation_id
            ORDER BY m1.created_at DESC
        ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'conversations': conversations}), 200
        
    except Exception as e:
        print(f"❌ Error fetching conversations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get messages for a conversation"""
    try:
        conversation_id = request.args.get('conversation_id')
        if not conversation_id:
            return jsonify({'error': 'Conversation ID required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        ''', (conversation_id,))
        
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'messages': messages}), 200
        
    except Exception as e:
        print(f"❌ Error fetching messages: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/messages', methods=['POST'])
def send_message():
    """Send a new message"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['sender_id', 'sender_name', 'sender_email', 
                   'receiver_id', 'receiver_name', 'receiver_email', 'message_text']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Generate conversation ID if not provided
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            # Create conversation ID from sorted user IDs
            user_ids = sorted([str(data['sender_id']), str(data['receiver_id'])])
            item_ref = f"_{data.get('item_id', 'general')}" if data.get('item_id') else ''
            conversation_id = f"conv_{user_ids[0]}_{user_ids[1]}{item_ref}"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (
                conversation_id, sender_id, sender_name, sender_email,
                receiver_id, receiver_name, receiver_email, message_text,
                item_id, item_type, item_title, is_read
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            conversation_id,
            data['sender_id'], data['sender_name'], data['sender_email'],
            data['receiver_id'], data['receiver_name'], data['receiver_email'],
            data['message_text'],
            data.get('item_id'), data.get('item_type'), data.get('item_title')
        ))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Message sent: {message_id} in conversation {conversation_id}")
        return jsonify({
            'success': True,
            'message_id': message_id,
            'conversation_id': conversation_id
        }), 201
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/messages/<int:message_id>/read', methods=['PUT'])
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE messages SET is_read = 1 WHERE message_id = ?', (message_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"❌ Error marking message read: {e}")
        return jsonify({'error': str(e)}), 500


# USER REVIEWS ENDPOINTS
@app.route('/api/user-reviews', methods=['POST'])
def create_user_review():
    """Create a review for another user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['reviewer_id', 'reviewer_name', 'reviewer_email',
                   'reviewed_user_id', 'reviewed_user_name', 'rating', 'review_type']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Validate rating
        if not (1 <= data['rating'] <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Validate review type
        if data['review_type'] not in ['FINDER', 'CLAIMER', 'APP']:
            return jsonify({'error': 'Invalid review type'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_reviews (
                reviewer_id, reviewer_name, reviewer_email,
                reviewed_user_id, reviewed_user_name,
                claim_id, item_id, item_title,
                rating, review_text, review_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['reviewer_id'], data['reviewer_name'], data['reviewer_email'],
            data['reviewed_user_id'], data['reviewed_user_name'],
            data.get('claim_id'), data.get('item_id'), data.get('item_title'),
            data['rating'], data.get('review_text', ''), data['review_type']
        ))
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ User review created: {review_id}")
        return jsonify({
            'success': True,
            'review_id': review_id
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating user review: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user-reviews/<int:user_id>', methods=['GET'])
def get_user_reviews(user_id):
    """Get reviews for a specific user"""
    try:
        review_type = request.args.get('type')  # FINDER, CLAIMER, APP, or None for all
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if review_type:
            cursor.execute('''
                SELECT * FROM user_reviews
                WHERE reviewed_user_id = ? AND review_type = ?
                ORDER BY created_at DESC
            ''', (user_id, review_type))
        else:
            cursor.execute('''
                SELECT * FROM user_reviews
                WHERE reviewed_user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
        
        reviews = [dict(row) for row in cursor.fetchall()]
        
        # Calculate average rating
        if reviews:
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        else:
            avg_rating = 0
        
        conn.close()
        
        return jsonify({
            'reviews': reviews,
            'total': len(reviews),
            'average_rating': round(avg_rating, 2)
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching user reviews: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user-reviews/stats/<int:user_id>', methods=['GET'])
def get_user_review_stats(user_id):
    """Get review statistics for a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_reviews,
                AVG(rating) as average_rating,
                SUM(CASE WHEN review_type = 'FINDER' THEN 1 ELSE 0 END) as finder_reviews,
                SUM(CASE WHEN review_type = 'CLAIMER' THEN 1 ELSE 0 END) as claimer_reviews,
                SUM(CASE WHEN review_type = 'APP' THEN 1 ELSE 0 END) as app_reviews
            FROM user_reviews
            WHERE reviewed_user_id = ?
        ''', (user_id,))
        
        stats = dict(cursor.fetchone())
        
        # Get rating distribution
        cursor.execute('''
            SELECT rating, COUNT(*) as count
            FROM user_reviews
            WHERE reviewed_user_id = ?
            GROUP BY rating
            ORDER BY rating DESC
        ''', (user_id,))
        
        rating_distribution = {row['rating']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'stats': stats,
            'rating_distribution': rating_distribution
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching review stats: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print("❌ Database not found!")
        print("📋 Please run: python generate_100k_database.py")
        print("   This will create the database with 100,000 realistic items")
        exit(1)
    
    print("🚀 Starting TrackeBack Comprehensive Backend")
    print(f"📂 Database: {DB_PATH}")
    print("📊 Features: 100K items, Kent State locations, Security verification")
    # Register profile management endpoints
    create_profile_endpoints(app)
    
    print("🌐 Server running on http://localhost:5000")
    print("🏠 API Info: http://localhost:5000/")
    print("💚 Health Check: http://localhost:5000/health")
    print("📱 Categories: http://localhost:5000/api/categories")
    print("📍 Locations: http://localhost:5000/api/locations")
    print("❌ Lost Items: http://localhost:5000/api/lost-items")
    print("✅ Found Items: http://localhost:5000/api/found-items")
    print("⭐ Reviews: http://localhost:5000/api/reviews")
    print("👤 Profile Management: http://localhost:5000/api/profile/{user_id}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)