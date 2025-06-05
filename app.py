from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Firebase Admin SDK
cred = credentials.Certificate('firebase/firebase-service-account.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/submit', methods=['POST'])
def submit_contact():
    try:
        data = request.json
        
        # Validate and sanitize inputs
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()

        # Validate email
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400

        # Create contact data
        contact_data = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'createdAt': firestore.SERVER_TIMESTAMP
        }

        # Add to Firestore
        contacts_ref = db.collection('contacts')
        doc_ref = contacts_ref.add(contact_data)
        
        print(f"Document added with ID: {doc_ref[1].id}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your message! We will get back to you soon.'
        })
        
    except Exception as e:
        print(f"Error in submit_contact: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)  # Return the actual error for debugging
        }), 500

@app.route('/verify-certificate', methods=['POST'])
def verify_certificate():
    try:
        data = request.json
        certificate_id = str(data.get('certificate_id', '')).strip()
        
        # Validate certificate ID format
        if not certificate_id:
            return jsonify({
                'success': False,
                'error': 'Certificate ID is required'
            }), 400
            
        # Query Firestore for the certificate
        certs_ref = db.collection('certificates')
        cert_docs = certs_ref.where('certificate_id', '==', certificate_id).limit(1).get()
        
        if not cert_docs:
            return jsonify({
                'success': False,
                'message': 'Certificate not found',
                'status': 'not_found'
            }), 404
            
        # Get the certificate data
        cert_data = cert_docs[0].to_dict()
        
        return jsonify({
            'success': True,
            'message': 'Certificate verified successfully',
            'status': 'verified',
            'data': {
                'name': cert_data.get('name', 'N/A'),
                'issue_date': cert_data.get('issue_date', 'N/A'),
                'certificate_id': cert_data.get('certificate_id', '')
            }
        })
    except Exception as e:
        print(f"Error in verify_certificate: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'error'
        }), 500

# Admin endpoint to add certificate IDs (for testing/administration)
@app.route('/admin/add-certificate', methods=['POST'])
def add_certificate():
    try:
        data = request.json
        certificate_id = str(data.get('certificate_id', '')).strip()
        name = str(data.get('name', '')).strip()
        issue_date = str(data.get('issue_date', '')).strip()
        
        # Validate input
        if not all([certificate_id, name, issue_date]):
            return jsonify({
                'success': False,
                'error': 'certificate_id, name, and issue_date are required'
            }), 400
            
        # Check if certificate ID already exists
        certs_ref = db.collection('certificates')
        existing = certs_ref.where('certificate_id', '==', certificate_id).limit(1).get()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Certificate ID already exists'
            }), 400
            
        # Add new certificate
        cert_data = {
            'certificate_id': certificate_id,
            'name': name,
            'issue_date': issue_date,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        certs_ref.add(cert_data)
        
        return jsonify({
            'success': True,
            'message': 'Certificate added successfully'
        })
    except Exception as e:
        print(f"Error in add_certificate: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
