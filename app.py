#importing modules
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from model import db, Customer, Professional, Admin
from model import Closed_Services, Services_status,Services,Service_Req, Service_History, Today_Services
import secrets
from flask_migrate import Migrate
import sqlite3
from sqlalchemy.sql import text
from datetime import datetime
from sqlalchemy import func, text
from app import db

app = Flask(__name__, instance_relative_config=True)
app.secret_key = secrets.token_hex(16)

# setting database URI
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///C:\Users\Ishita Tayal\Desktop\household_services.db"  # Absolute path for SQLite

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)
migrate = Migrate(app, db)

# Create the tables
with app.app_context():
    db.create_all()

#BEGINNING OF ROUTES
@app.route("/")
def index():
    return render_template("index.html")

# SIGN UP AND LOGIN ROUTES
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # query to verify if the user is a customer
        customer =  Customer.query.filter_by(email=email, password=password).first()
        if customer:
            session['customer_id'] = customer.customer_id
            return redirect(url_for('customer_dashboard'))  # Redirect to Customer Dashboard

        # query to verify if the user is a professional
        professional = Professional.query.filter_by(email=email, password=password).first()
        if professional:
            session['professional_id'] = professional.professional_id
            return redirect(url_for('professional_dashboard'))  # Redirect to Professional Dashboard

        # query to verify if the user is an admin
        admin = Admin.query.filter_by(email=email, password=password).first()
        if admin:
            return redirect(url_for('admin_dashboard'))  # Redirect to Admin Dashboard

        # if no match is found, flash an error message
        flash('Invalid credentials. Please try again.', 'danger')
        return redirect(url_for('user_login'))  # redirect back to login page

    return render_template('user/login.html')

@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['fullname']
        address = request.form['address']
        pincode = request.form['pincode']

        # Check if the email exists in the Customer table
        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer:
            flash('Already Registered with this email. Please login.', 'danger')
            return render_template('user/register.html')  # same page with the flash message

        # Check if the email exists in the Professional table
        existing_professional = Professional.query.filter_by(email=email).first()
        if existing_professional:
            flash('Already Registered with this email. Please login.', 'danger')
            return render_template('user/register.html')  # same page with the flash message

        # Create a new Customer object
        new_customer = Customer(
            email=email,
            password=password,
            full_name=full_name,
            address=address,
            pincode=pincode,
            role='customer'
        )

        # Add to the database
        db.session.add(new_customer)
        db.session.commit()

        flash('Registered Successfully! Please login to continue.', 'success')
        return render_template('user/register.html')  # same page with the flash message

    return render_template('user/register.html')

@app.route('/user/service_prof_signup', methods=['GET','POST'])
def service_prof_signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['fullname']
        service_name = request.form['service_name']
        experience = request.form['experience']
        document = request.files['documents']
        address = request.form['address']
        pincode = request.form['pincode']

        # check for email in cust table
        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer:
            flash('Already Registered with this email. Please login.', 'danger')
            return render_template('user/service_prof_signup.html')  # same page with the flash message

        # check for email in the prof table
        existing_professional = Professional.query.filter_by(email=email).first()
        if existing_professional:
            flash('Already Registered with this email. Please login.', 'danger')
            return render_template('user/service_prof_signup.html')  # same page with the flash message

        # attached doc is saved in binary format
        document_data = document.read() if document else None

        # new_professional to append entry in the database
        new_professional = Professional(
            email=email,
            password=password,
            full_name=full_name,
            service_name=service_name,
            experience=experience,
            document=document_data,  # store PDF as binary data
            address=address,
            pincode=pincode,
            role='professional'
        )

        # add to the database
        db.session.add(new_professional)
        db.session.commit()

        flash('Registered Successfully! Please login to continue.', 'success')
        return render_template('user/service_prof_signup.html')  # same page with the success message

    return render_template('user/service_prof_signup.html')

def get_logged_in_professional():
    # validate professional who logged in
    professional_id = session.get('professional_id')
    if professional_id:
        return Professional.query.get(professional_id)  # fetch the professional-id from the database
    return None  # return none when no prof has logged in

@app.route('/professional/login', methods=['GET'])
def service_professional_login():
    return render_template('user/login.html')

# ADMIN ROUTES
@app.route('/user/admin_profile', methods=['GET'])
def admin_profile():
    return render_template('/user/admin_profile.html')

@app.route('/admin/login', methods=['GET'])
def admin_login():
    return render_template('user/login.html')

@app.route('/user/admin_add_service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        # get the required data from the form data
        service_id = request.form['service_id']
        service_name = request.form['service_name']
        base_price = request.form['base_price']

        # store new service data
        new_service = Services(id=service_id,service_name=service_name, base_price=base_price)
        db.session.add(new_service)
        db.session.commit()

        return redirect(url_for('admin_dashboard'))  # redirect to the admin dashboard where it was previously

    return render_template('user/admin_add_service.html')

# route to edit a service
@app.route('/user/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Services.query.get_or_404(service_id)
    
    if request.method == 'POST':
        service.service_name = request.form['service_name']
        service.base_price = request.form['base_price']
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('user/edit_service.html', service=service)

# route to delete a service
@app.route('/user/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Services.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# route to approve a professional
@app.route('/user/approve_professional/<int:professional_id>', methods=['POST'])
def approve_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    professional.status = 'Approved'  
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# route to reject a professional
@app.route('/user/reject_professional/<int:professional_id>', methods=['POST'])
def reject_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    professional.status = 'Rejected' 
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# route to delete a professional
@app.route('/user/delete_professional/<int:professional_id>', methods=['POST'])
def delete_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    db.session.delete(professional)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/user/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # get all services
    services = Services.query.all()

    # retrieve todays services and include professional names
    today_services_query = (
        db.session.query(
            Today_Services.id,
            Today_Services.professional_id,
            Professional.full_name.label('professional_name')
        )
        .outerjoin(Professional, Today_Services.professional_id == Professional.professional_id)
        .all()
    )

    # Convert today_services_query results to dictionaries
    today_services = [dict(id=row.id, professional_id=row.professional_id, professional_name=row.professional_name) for row in today_services_query]

    # Query closed services and join with professionals to get their names
    closed_services_query = (
        db.session.query(
            Closed_Services.id,
            Closed_Services.pid.label('professional_id'),
            Closed_Services.date,
            Professional.full_name.label('professional_name')
        )
        .outerjoin(Professional, Closed_Services.pid == Professional.professional_id)
        .all()
    )

    # Convert closed_services_query results to dictionaries
    closed_services = [dict(id=row.id, professional_id=row.professional_id, date=row.date, professional_name=row.professional_name) for row in closed_services_query]

    # Query service history (no join needed, already have professional_name)
    service_history_query = (
        db.session.query(
            Service_History.service_id.label('id'),
            Service_History.service_name,
            Service_History.professional_name,
            Service_History.status
        )
        .all()
    )

    # Convert service_history_query results to dictionaries
    service_history = [dict(id=row.id, service_name=row.service_name, professional_name=row.professional_name, status=row.status) for row in service_history_query]

    # Query all professionals
    professionals = db.session.query(Professional).all()

    # Format data for template
    service_requests = []

    # Service history
    for history in service_history:
        # Map status codes to full names (R -> Requested, C -> Closed)
        status = 'R' if history['status'] == 'Requested' else 'C'
        
        service_requests.append({
            'id': history['id'],
            'professional': history['professional_name'],
            'service_name': history['service_name'],  # Placeholder if no date available in history
            'status': status
        })

    # Render data in the template
    return render_template(
        'user/admin_dashboard.html',
        services=services,
        professionals=professionals,  # Pass professionals data here
        service_requests=service_requests
    )

# Admin Routes
@app.route('/user/admin_search', methods=['GET', 'POST'])
def admin_search():
    # Initialize search results and criteria
    results, criteria = [], None

    if request.method == 'POST':
        criteria = request.form.get('searchBy')
        search_input = request.form.get('searchText')

        if not search_input:
            flash('Please enter search text.', 'warning')
            return redirect(url_for('admin_search'))

        # Define model fields to search based on selected criteria
        search_targets = {
            'services': Services.service_name,
            'service requests': Service_Req.service_name,
            'customers': Customer.full_name,
            'professionals': Professional.full_name
        }

        # Execute search if valid criteria selected
        if criteria in search_targets:
            target_field = search_targets[criteria]
            model = target_field.class_
            results = model.query.filter(target_field.ilike(f"%{search_input}%")).all()
        else:
            flash('Invalid search criteria.', 'danger')

    return render_template('user/admin_search.html', search_results=results, search_by=criteria)

@app.route('/user/admin_summary', methods=['GET'])
def admin_summary():
    # Aggregate ratings data, grouping by rating value
    rating_counts = (
        db.session.query(Closed_Services.rating, func.count())
        .group_by(Closed_Services.rating)
        .all()
    )
    ratings_data = {str(rating): count for rating, count in rating_counts}

    # Count total service requests in different categories
    received_count = db.session.query(func.count()).select_from(Service_History).scalar()
    closed_count = db.session.query(func.count()).select_from(Closed_Services).scalar()
    rejected_count = sum(count for status, count in db.session.query(Services_status.status, func.count()).group_by(Services_status.status).all() if status == 'R')

    service_requests_summary = {
        'Received': received_count,
        'Closed': closed_count,
        'Rejected': rejected_count
    }

    return render_template('user/admin_summary.html', ratings_data=ratings_data, service_requests_data=service_requests_summary)

# CUSTOMER ROUTES
@app.route('/user/customer_dashboard', methods=['GET'])
def customer_dashboard():
    customer_id = session.get('customer_id')
    history_records = Service_History.query.filter_by(id=customer_id).all()
    available_services = Services.query.all()
    return render_template('user/customer_dashboard.html', services=available_services, service_history=history_records)

@app.route('/user/customer_profile', methods=['GET'])
def customer_profile():
    customer_id = session.get('customer_id')
    customer_info = Customer.query.filter_by(customer_id=customer_id).one()
    return render_template('user/customer_profile.html', customer=customer_info)

@app.route('/user/customer_remarks', methods=['GET'])
def customer_remarks():
    return render_template('user/customer_remarks.html')

@app.route('/user/customer_summary', methods=['GET'])
def customer_summary():
    customer_id = session.get('customer_id')

    # Count total requests and closed requests for the customer
    total_requests = db.session.query(func.count(Service_History.id)).filter(Service_History.id == customer_id).scalar()
    closed_requests = db.session.query(func.count(Service_History.id)).filter(Service_History.id == customer_id, Service_History.status == 'Closed').scalar()

    # Calculate assigned requests by subtracting closed from total
    assigned_requests = total_requests - closed_requests

    # Prepare data summary
    service_summary_data = {
        'Requested': total_requests,
        'Closed': closed_requests,
        'Assigned': assigned_requests
    }

    return render_template('user/customer_summary.html', service_history_data=service_summary_data)

@app.route('/user/submit_service_remarks', methods=['POST'])
def submit_service_remarks():
    customer_id = session.get('customer_id')
    customer_info = Customer.query.filter_by(customer_id=customer_id).one()
    service_id = request.form.get('service_id')

    # Find the relevant professional
    professional_info = (
        Professional.query
        .join(Service_History, Professional.full_name == Service_History.professional_name)
        .filter(Service_History.service_id == service_id, Professional.full_name == Service_History.professional_name)
        .one()
    )

    # Create a record for closed service
    new_closed_service = Closed_Services(
        customer_name=customer_info.full_name,
        email=customer_info.email,
        location=customer_info.address,
        date=datetime.today().date(),
        cid=customer_info.customer_id,
        pid=professional_info.professional_id,
        rating=request.form.get('rating')
    )
    db.session.add(new_closed_service)
    db.session.commit()
    return redirect(url_for('customer_dashboard'))

@app.route('/user/customer_search', methods=['GET', 'POST'])
def customer_search():
    # Initialize search results and criteria
    results, criteria = [], None

    if request.method == 'POST':
        criteria = request.form.get('searchBy')
        search_text = request.form.get('searchInput')

        if not search_text:
            flash('Please enter search text.', 'warning')
            return redirect(url_for('customer_search'))

        # Define search criteria and fields for professionals
        search_filters = {
            'service_name': Professional.service_name,
            'pin_code': Professional.pincode,
            'location': Professional.address
        }

        # Execute search query if criteria is valid
        if criteria in search_filters:
            filter_field = search_filters[criteria]
            results = Professional.query.filter(filter_field.ilike(f"%{search_text}%"), Professional.status == "Approved").all()
        else:
            flash('Invalid search criteria.', 'danger')

    return render_template('user/customer_search.html', search_results=results, search_by=criteria)

@app.route('/book_service', methods=['POST'])
def book_service():
    # Retrieve form data
    customer_id = session['customer_id']  # Retrieve customer_id from session
    customer = Customer.query.filter_by(customer_id=customer_id).one()

    # Create a new booking instance
    new_booking = Today_Services(
        customer_name=customer.full_name,
        email=customer.email,
        location=customer.address,
        customer_id=customer.customer_id,
        professional_id=request.form.get('id')
    )
    
    new_booking_cust = Service_History(
        id = customer.customer_id,
        service_name = request.form.get('service_name'),
        professional_name=request.form.get('professional_name'),
        email=request.form.get('email'),
        status = "Requested"
    )

    # Add to the session and commit to the database
    db.session.add(new_booking)
    db.session.add(new_booking_cust)
    db.session.commit()

    flash('Booking successful!', 'success')

    # Redirect back to the main page or to a confirmation page
    return redirect(url_for('customer_dashboard'))

@app.route('/close_service', methods=['POST'])
def close_service():
    # Retrieve form data
    service_id = request.form.get('service_id')
    service = Service_History.query.filter_by(service_id = service_id).one()
    if service:
        service.status = "Closed"
        db.session.commit()

    professional = Professional.query.join(Service_History, Professional.full_name == Service_History.professional_name).filter(Service_History.service_id == service_id).filter(Professional.full_name == Service_History.professional_name).one()
    customer_id = session['customer_id']
    
    db.session.query(Today_Services).filter_by(professional_id = professional.professional_id, customer_id = customer_id ).delete()
    db.session.commit()

    # Redirect back to the main page or to a confirmation page
    return render_template('user/customer_remarks.html', service = service)

@app.route('/search_services', methods=['POST'])
def search_services():
    search_results = []
    search_by = None  # Initialize search_by variable

    if request.method == 'POST':  # Handle POST request
        search_by = request.form.get('service_type')
        # Search in the 'services' table for service_name
        search_results = Professional.query.filter(Professional.service_name.ilike(f"%{search_by}%"),Professional.status == "Approved").all()

    customer_id = session['customer_id']
    service_history = Service_History.query.filter_by(id=customer_id).all()
    services = Services.query.all()

    return render_template('user/customer_dashboard.html', services=services,service_history=service_history,search_results=search_results, search_by=search_by)

#PROFESSIONAL ROUTES
@app.route('/user/professional_dashboard', methods=['GET'])
def professional_dashboard():
    current_professional = get_logged_in_professional()
    prof_id = session.get('professional_id')  # Assuming professional's ID is stored in session

    # Query for today and closed services assigned to the professional
    active_services = Today_Services.query.filter_by(professional_id=prof_id).all()
    completed_services = Closed_Services.query.filter_by(pid=prof_id).all()

    # Render the template with dynamic data
    return render_template('user/professional_dashboard.html', 
                           professional=current_professional, 
                           today_services=active_services, 
                           closed_services=completed_services)

@app.route('/accept_service/<int:service_id>', methods=['POST'])
def accept_service(service_id):
    # Retrieve the service from Today_Services by ID
    selected_service = Today_Services.query.get(service_id)
    if selected_service:
        # Add to Services_status with an 'Accepted' status
        accepted_service = Services_status(
            customer_name=selected_service.customer_name,
            email=selected_service.email,
            location=selected_service.location,
            status='A'
        )
        db.session.add(accepted_service)
        db.session.delete(selected_service)  # Remove from Today's Services
        db.session.commit()
    return redirect(url_for('professional_dashboard'))

@app.route('/reject_service/<int:service_id>', methods=['POST'])
def reject_service(service_id):
    # Retrieve the service from Today_Services by ID
    selected_service = Today_Services.query.get(service_id)
    if selected_service:
        # Add to Services_status with a 'Rejected' status
        rejected_service = Services_status(
            customer_name=selected_service.customer_name,
            email=selected_service.email,
            location=selected_service.location,
            status='R'
        )
        db.session.add(rejected_service)
        db.session.delete(selected_service)  # Remove from Today's Services
        db.session.commit()
    return redirect(url_for('professional_dashboard'))

@app.route('/user/professional_view_profile/<int:professional_id>', methods=['GET'])
def professional_view_profile(professional_id):
    # Fetch the professional by ID
    prof = Professional.query.get_or_404(professional_id)
    return render_template('user/professional_view_profile.html', professional=prof)

@app.route('/user/professional_edit_profile/<int:professional_id>', methods=['GET', 'POST'])
def professional_edit_profile(professional_id):
    prof = Professional.query.get_or_404(professional_id)

    if request.method == 'POST':
        # Get and validate form data (excluding role/status fields)
        email = request.form.get('email', prof.email)
        new_password = request.form.get('password')
        full_name = request.form.get('fullname')
        service = request.form.get('service_name')
        years_experience = request.form.get('experience')
        uploaded_document = request.files.get('document')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        # Check required fields
        if not all([full_name, service, years_experience, address, pincode]):
            flash('All required fields must be completed.', 'danger')
            return render_template('user/professional_edit_profile.html', professional=prof)
        
        if new_password:
            prof.password = new_password

        # Update professional information
        prof.email = email
        prof.full_name = full_name
        prof.service_name = service
        prof.experience = int(years_experience) if years_experience else 0
        if uploaded_document:
            prof.document = uploaded_document.read()
        prof.address = address
        prof.pincode = pincode

        # Commit updated profile
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('professional_view_profile', professional_id=prof.professional_id))
        except Exception as error:
            db.session.rollback()
            flash(f"Error: {error}", 'danger')
            return render_template('user/professional_edit_profile.html', professional=prof)

    return render_template('user/professional_edit_profile.html', professional=prof)

@app.route('/user/professional_summary', methods=['GET'])
def professional_summary():
    current_professional = get_logged_in_professional()
    
    if not current_professional:
        return redirect(url_for('user_login'))  # Redirect if no professional is logged in

    # Fetch rating data for the logged-in professional
    rating_data = (
        db.session.query(Closed_Services.rating, func.count())
        .filter(Closed_Services.pid == current_professional.professional_id)
        .group_by(Closed_Services.rating)
        .all()
    )

    ratings_summary = {str(rate): count for rate, count in rating_data}

    # Fetch service request data for the logged-in professional
    service_data = (
        db.session.query(Service_History.status, func.count())
        .filter(Service_History.professional_name == current_professional.full_name)
        .group_by(Service_History.status)
        .all()
    )

    requests_summary = {
        'Received': sum(count for _, count in service_data),
        'Closed': sum(count for status, count in service_data if status == 'Closed'),
        'Rejected': sum(count for status, count in service_data if status == 'Requested')
    }

    return render_template(
        'user/professional_summary.html',
        ratings_data=ratings_summary,
        service_requests_data=requests_summary
    )

@app.route('/user/professional_search', methods=['GET', 'POST'])
def professional_search():
    search_results = []
    if request.method == 'POST':
        search_criterion = request.form.get('searchBy')
        search_input = request.form.get('searchText')

        if not search_input:
            flash('Please enter search text.', 'warning')
            return redirect(url_for('professional_search'))

        # Search database based on selected criterion
        if search_criterion == 'date':
            search_results = Closed_Services.query.filter(Closed_Services.date == search_input, Closed_Services.pid == session['professional_id']).all()
        elif search_criterion == 'location':
            search_results = Closed_Services.query.filter(Closed_Services.location.ilike(f"%{search_input}%"), Closed_Services.pid == session['professional_id']).all()
        elif search_criterion == 'pincode':
            search_results = Closed_Services.query.filter(Closed_Services.location.contains(search_input), Closed_Services.pid == session['professional_id']).all()
        elif search_criterion == 'customer':
            search_results = Closed_Services.query.filter(Closed_Services.customer_name.ilike(f"%{search_input}%"), Closed_Services.pid == session['professional_id']).all()
        else:
            flash('Invalid search criteria.', 'danger')
    
    return render_template('user/professional_search.html', search_results=search_results)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    logout_redirect = redirect(url_for('user_login'))
    logout_redirect.set_cookie('session', '', expires=0)  # Clear session cookie
    return logout_redirect

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)
