import os, math, webbrowser, uuid
from datetime import datetime
from threading import Timer
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__); app.secret_key = "localeats_final_sprint1"
UPLOAD_FOLDER = 'uploads'; ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}; app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER; os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename): return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def file_extension(filename): return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371; dlat = math.radians(lat2 - lat1); dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

users_db = {
    "ADMIN1": {"role": "Admin", "name": "System Admin", "status": "Active"},
    "C303": {"role": "Customer", "name": "Bassant Ibrahim", "status": "Active"},
    "VEND101": {"role": "Vendor", "name": "Pizza House", "status": "Active"}
}
pending_vendors, pending_drivers = {}, {}

vendors = [
    {"name":"Pizza House","lat":30.51,"lon":30.52,"cuisine":"Italian","rating":4.5,"fee":20,"time":30},
    {"name":"Koshary Beity","lat":30.6,"lon":30.4,"cuisine":"Egyptian","rating":4.8,"fee":10,"time":20},
    {"name":"Burger Zone","lat":31.2,"lon":29.9,"cuisine":"American","rating":3.9,"fee":25,"time":40}
]

# Menu DB: { vendor_name: { "categories": ["Appetizers", ...], "items": { item_id: {...} } } }
menu_db = {}

def get_vendor_menu(vendor_name):
    if vendor_name not in menu_db:
        menu_db[vendor_name] = {"categories": [], "items": {}}
    return menu_db[vendor_name]

DECLINE_REASONS = [
    "Incomplete application details",
    "Invalid or unclear uploaded documents",
    "Expired driver's license or ID",
    "Bank account or mobile wallet details missing/invalid",
    "Vehicle information missing or invalid",
    "Failed verification checks",
    "Application does not meet platform requirements"
]

COMMON_STYLE = """
<style>
:root{--le-green:#4CAF50;--le-dark:#2e7d32;--le-light:#e8f5e9;--bg:#f4f7f6;--text:#222;--muted:#666;--danger:#d32f2f;--danger-dark:#b71c1c;--card-shadow:0 10px 25px rgba(0,0,0,0.06);--border:#e3e7e5;}
*{box-sizing:border-box;} body{font-family:'Segoe UI',sans-serif;background:var(--bg);margin:0;color:var(--text);}
.page{max-width:1250px;margin:30px auto;padding:0 20px 40px;} .card{background:white;border-radius:16px;box-shadow:var(--card-shadow);padding:24px;margin-bottom:24px;}
.center-card{max-width:520px;margin:60px auto;text-align:center;} .logo{color:var(--le-green);font-weight:800;font-size:34px;margin-bottom:8px;}
.subtitle{color:var(--muted);font-size:14px;margin-top:0;} h1,h2,h3,h4{margin-top:0;}
.btn{background:var(--le-green);color:white;padding:11px 16px;border:none;border-radius:10px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block;font-size:14px;}
.btn:hover{background:var(--le-dark);} .btn-secondary{background:#666;} .btn-secondary:hover{background:#4f4f4f;}
.btn-danger{background:var(--danger);} .btn-danger:hover{background:var(--danger-dark);}
.btn-outline{background:white;color:var(--le-green);border:1px solid var(--le-green);} .btn-outline:hover{background:var(--le-light);}
.btn-warning{background:#f57c00;color:white;} .btn-warning:hover{background:#e65100;}
.btn-sm{padding:8px 12px;font-size:13px;border-radius:8px;} .full-width{width:100%;} .btn-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;}
input,select,textarea{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;font-size:14px;font-family:inherit;}
label{font-size:12px;color:var(--muted);display:block;text-align:left;margin-top:10px;}
.progress-container{display:flex;justify-content:space-between;margin:20px 0 40px;position:relative;} .progress-line{position:absolute;top:15px;left:0;height:2px;background:#ddd;width:100%;z-index:1;}
.step{width:30px;height:30px;border-radius:50%;background:#ddd;z-index:2;display:flex;align-items:center;justify-content:center;font-size:12px;color:white;font-weight:bold;position:relative;} .step.active{background:var(--le-green);}
.step-label{position:absolute;top:35px;font-size:10px;color:#888;text-transform:uppercase;white-space:nowrap;}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:22px;} .topbar-left h1{margin-bottom:4px;} .muted{color:var(--muted);}
.grid-2{display:grid;grid-template-columns:1.1fr 1fr;gap:24px;} .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;}
.stat-box{background:white;border-radius:14px;padding:18px;box-shadow:var(--card-shadow);} .stat-label{color:var(--muted);font-size:13px;margin-bottom:8px;} .stat-value{font-size:28px;font-weight:800;color:var(--le-dark);}
table{width:100%;border-collapse:collapse;} th,td{padding:14px 12px;border-bottom:1px solid var(--border);text-align:left;vertical-align:middle;font-size:14px;}
th{color:#333;background:#fafcfa;font-size:13px;text-transform:uppercase;letter-spacing:.3px;}
.badge{display:inline-block;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:700;} .badge-pending{background:#fff3e0;color:#e65100;}
.badge-live{background:#e8f5e9;color:#1b5e20;} .badge-customer{background:#e3f2fd;color:#0d47a1;} .badge-vendor{background:#f3e5f5;color:#6a1b9a;} .badge-driver{background:#fff8e1;color:#8d6e00;}
.badge-instock{background:#e8f5e9;color:#1b5e20;} .badge-outofstock{background:#ffebee;color:#c62828;}
.info-list{display:grid;gap:14px;} .info-item{background:#fafcfa;border:1px solid var(--border);border-radius:12px;padding:14px;} .info-label{font-size:12px;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.3px;} .info-value{font-size:15px;font-weight:600;word-break:break-word;}
.preview-box{border:1px solid var(--border);border-radius:14px;overflow:hidden;background:#fafafa;min-height:320px;} .preview-frame{width:100%;height:520px;border:none;background:white;} .preview-image{width:100%;max-height:520px;object-fit:contain;display:block;background:white;}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px;} .empty-state{text-align:center;padding:34px 16px;color:var(--muted);border:1px dashed var(--border);border-radius:14px;background:#fcfdfc;}
.success-box{border:2px solid #c8e6c9;background:#f1f8f2;border-radius:12px;padding:18px;margin-top:12px;} .danger-box{border:2px solid #ffcdd2;background:#fff5f5;border-radius:12px;padding:18px;margin-top:12px;}
.choice-card{display:block;padding:18px;border:1px solid var(--border);border-radius:14px;text-decoration:none;color:var(--text);text-align:left;background:#fcfdfc;} .choice-card:hover{background:var(--le-light);}
.section-title{margin:30px 0 12px;}
.browse-wrap{display:flex;gap:20px;align-items:flex-start;} .browse-sidebar{width:260px;padding:20px;background:white;border-radius:16px;box-shadow:var(--card-shadow);}
.browse-content{flex:1;} .browse-card{background:white;padding:20px;border-radius:14px;margin-bottom:15px;box-shadow:0 5px 15px rgba(0,0,0,0.05);}
/* Menu management styles */
.menu-wrap{display:flex;gap:20px;align-items:flex-start;}
.menu-sidebar{width:240px;flex-shrink:0;background:white;border-radius:16px;box-shadow:var(--card-shadow);padding:20px;}
.menu-content{flex:1;}
.category-item{padding:10px 14px;border-radius:10px;cursor:pointer;font-size:14px;font-weight:600;margin-bottom:6px;text-decoration:none;display:block;color:var(--text);}
.category-item:hover{background:var(--le-light);}
.category-item.active{background:var(--le-light);color:var(--le-dark);}
.menu-item-row{background:white;border-radius:14px;box-shadow:0 4px 12px rgba(0,0,0,0.05);padding:16px 20px;display:flex;align-items:center;gap:16px;margin-bottom:12px;}
.menu-item-img{width:60px;height:60px;border-radius:10px;object-fit:cover;background:#f0f0f0;flex-shrink:0;}
.menu-item-img-placeholder{width:60px;height:60px;border-radius:10px;background:#e8f5e9;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;}
.menu-item-info{flex:1;}
.menu-item-name{font-weight:700;font-size:15px;margin-bottom:3px;}
.menu-item-price{color:var(--le-dark);font-weight:700;font-size:14px;}
.menu-item-desc{color:var(--muted);font-size:13px;margin-top:2px;}
.menu-item-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.out-of-stock-row{opacity:0.55;}
/* Customer menu styles */
.cust-category{margin-bottom:28px;}
.cust-category-title{font-size:17px;font-weight:800;color:var(--le-dark);margin-bottom:12px;padding-bottom:6px;border-bottom:2px solid var(--le-light);}
.cust-item{background:white;border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:center;gap:14px;box-shadow:0 3px 8px rgba(0,0,0,0.04);}
.cust-item.oos{opacity:0.5;}
.cust-item-img{width:54px;height:54px;border-radius:8px;object-fit:cover;background:#f0f0f0;flex-shrink:0;}
.cust-item-img-placeholder{width:54px;height:54px;border-radius:8px;background:#e8f5e9;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}
.cust-item-name{font-weight:700;font-size:14px;}
.cust-item-price{color:var(--le-dark);font-weight:700;font-size:13px;margin-top:2px;}
.cust-item-desc{color:var(--muted);font-size:12px;margin-top:2px;}
@media (max-width:900px){.grid-2,.stats{grid-template-columns:1fr;}.topbar,.browse-wrap,.menu-wrap{flex-direction:column;align-items:flex-start;} table{font-size:13px;} .browse-sidebar,.menu-sidebar{width:100%;}}
</style>
"""

def next_id(prefix):
    max_num = 100
    for uid in users_db:
        if uid.startswith(prefix):
            try: max_num = max(max_num, int(uid.replace(prefix, "")))
            except ValueError: pass
    return f"{prefix}{max_num + 1}"

def render_file_preview(filename):
    ext, file_url = file_extension(filename), url_for('uploaded_file', filename=filename)
    if ext == 'pdf': return f'<div class="preview-box"><iframe src="{file_url}" class="preview-frame"></iframe></div>'
    if ext in ['png', 'jpg', 'jpeg']: return f'<div class="preview-box"><img src="{file_url}" alt="Uploaded document" class="preview-image"></div>'
    return f'<div class="preview-box" style="padding:20px;"><p>Preview not available.</p><a class="btn btn-outline btn-sm" href="{file_url}" target="_blank">Open File</a></div>'

def decline_reason_options(): return "".join([f'<option value="{r}">{r}</option>' for r in DECLINE_REASONS])

@app.route('/')
def login_page():
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">LocalEats</div><h2>Login</h2><p class="subtitle">Sign in with your user ID</p><form action="/auth" method="POST"><input type="text" name="uid" placeholder="Enter ID (Admin: ADMIN1, Customer: C303)" required><button type="submit" class="btn full-width">Sign In</button></form><p style="font-size:13px;margin-top:20px;">Want to join LocalEats? <a href="/register" style="color:var(--le-green);text-decoration:none;font-weight:bold;">Register</a></p></div>""")

@app.route('/auth', methods=['POST'])
def auth():
    uid = request.form.get('uid', '').upper().strip()
    if uid in users_db:
        role, name = users_db[uid]["role"].lower(), users_db[uid]["name"]
        if role == "admin": return redirect(url_for("admin_dashboard"))
        if role == "customer": return redirect(url_for("customer_dashboard", uid=uid, name=name))
        if role == "vendor": return redirect(url_for("vendor_dashboard", uid=uid, name=name))
        if role == "driver": return redirect(url_for("driver_dashboard", uid=uid, name=name))
    return "<h3>ID Pending or Invalid.</h3><a href='/'>Back</a>"

@app.route('/register')
def register_choice():
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">LocalEats</div><h2>Choose Registration Type</h2><p class="subtitle">Select how you want to sign up</p><div class="btn-row" style="flex-direction:column;"><a class="choice-card" href="/register/vendor"><h3 style="margin-bottom:8px;">Vendor Registration</h3><div class="muted">Register your restaurant and upload hygiene documents.</div></a><a class="choice-card" href="/register/driver"><h3 style="margin-bottom:8px;">Driver Registration</h3><div class="muted">Register as a delivery driver and upload your required documents.</div></a></div><div style="margin-top:18px;"><a href="/" class="btn btn-secondary">Back to Login</a></div></div>""")

@app.route('/register/vendor')
def register_vendor():
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">LocalEats</div><div class="progress-container"><div class="progress-line"></div><div class="step active">1<span class="step-label" style="left:0">Apply</span></div><div class="step">2<span class="step-label" style="left:-10px">Review</span></div><div class="step">3<span class="step-label" style="right:0">Live</span></div></div><form action="/submit_vendor_app" method="POST" enctype="multipart/form-data"><input type="text" name="vname" placeholder="Restaurant Name" required><input type="text" name="vaddress" placeholder="Address" required><label>Upload Hygiene Doc (PDF/JPG/PNG)</label><input type="file" name="vdoc" accept=".pdf,.jpg,.png,.jpeg" required><button type="submit" class="btn full-width">Submit Vendor Application</button></form></div>""")

@app.route('/register/driver')
def register_driver():
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">LocalEats</div><div class="progress-container"><div class="progress-line"></div><div class="step active">1<span class="step-label" style="left:0">Apply</span></div><div class="step">2<span class="step-label" style="left:-10px">Review</span></div><div class="step">3<span class="step-label" style="right:0">Live</span></div></div><form action="/submit_driver_app" method="POST" enctype="multipart/form-data"><input type="text" name="dname" placeholder="Full Name" required><input type="text" name="phone" placeholder="Phone Number" required><input type="text" name="vehicle_type" placeholder="Vehicle Type (Car / Bike / Scooter)" required><input type="text" name="vehicle_plate" placeholder="Vehicle Plate Number" required><input type="text" name="bank_wallet" placeholder="Bank Account or Mobile Wallet Details" required><label>Upload Clear Driver's License Photo (PDF/JPG/PNG)</label><input type="file" name="license_file" accept=".pdf,.jpg,.png,.jpeg" required><label>Upload Clear National ID Photo (PDF/JPG/PNG)</label><input type="file" name="nid_file" accept=".pdf,.jpg,.png,.jpeg" required><button type="submit" class="btn full-width">Submit Driver Application</button></form></div>""")

@app.route('/submit_vendor_app', methods=['POST'])
def submit_vendor_app():
    vname, vaddress, file = request.form.get('vname', '').strip(), request.form.get('vaddress', '').strip(), request.files.get('vdoc')
    if not vname or not vaddress: return "Missing application details."
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{vname}_{file.filename}"); file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        pending_vendors[vname] = {"name": vname, "address": vaddress, "file": filename, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": "Vendor", "status": "Inactive - Pending Admin Approval"}
        vendors.append({"name": vname, "lat": 30.5, "lon": 30.5, "cuisine": "Various", "rating": 4.0, "fee": 20, "time": 30})
        return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">LocalEats</div><div style="border:2px dashed orange;padding:20px;border-radius:10px;background:#fffdf5;"><h3 style="color:orange;">Vendor Application Pending</h3><p>Documents for <strong>{vname}</strong> are being reviewed.</p><p style="font-size:12px;">The file <b>{filename}</b> was successfully uploaded.</p><p style="font-size:12px;">Your profile will remain inactive until approved by an Admin.</p></div><a href="/" class="btn full-width">Return Home</a></div>""")
    return "Invalid File Type."

@app.route('/submit_driver_app', methods=['POST'])
def submit_driver_app():
    dname = request.form.get('dname', '').strip(); phone = request.form.get('phone', '').strip(); vehicle_type = request.form.get('vehicle_type', '').strip()
    vehicle_plate = request.form.get('vehicle_plate', '').strip(); bank_wallet = request.form.get('bank_wallet', '').strip()
    license_file, nid_file = request.files.get('license_file'), request.files.get('nid_file')
    if not all([dname, phone, vehicle_type, vehicle_plate, bank_wallet, license_file, nid_file]): return "Missing driver registration details."
    if allowed_file(license_file.filename) and allowed_file(nid_file.filename):
        license_name = secure_filename(f"{dname}_license_{license_file.filename}"); nid_name = secure_filename(f"{dname}_nid_{nid_file.filename}")
        license_file.save(os.path.join(app.config['UPLOAD_FOLDER'], license_name)); nid_file.save(os.path.join(app.config['UPLOAD_FOLDER'], nid_name))
        pending_drivers[dname] = {"name": dname, "phone": phone, "vehicle_type": vehicle_type, "vehicle_plate": vehicle_plate, "bank_wallet": bank_wallet, "license_file": license_name, "nid_file": nid_name, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": "Driver", "status": "Inactive - Pending Admin Approval"}
        return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">LocalEats</div><div style="border:2px dashed orange;padding:20px;border-radius:10px;background:#fffdf5;"><h3 style="color:orange;">Driver Application Pending</h3><p>Registration for <strong>{dname}</strong> was submitted successfully.</p><p style="font-size:12px;">Your driver's license, national ID, vehicle details, and payout details were received.</p><p style="font-size:12px;">Your driver profile will remain inactive until approved by an Admin.</p></div><a href="/" class="btn full-width">Return Home</a></div>""")
    return "Invalid File Type."

@app.route('/uploads/<path:filename>')
def uploaded_file(filename): return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin')
def admin_dashboard():
    pending_vendor_rows = "".join([f"""<tr><td>{i}</td><td>{d['name']}</td><td>Vendor</td><td>{d['submitted_at']}</td><td><span class="badge badge-pending">Pending</span></td><td><a class="btn btn-sm btn-outline" href="/admin/vendor/{name}">Open</a></td></tr>""" for i, (name, d) in enumerate(pending_vendors.items(), start=1)])
    pending_driver_rows = "".join([f"""<tr><td>{i}</td><td>{d['name']}</td><td>Driver</td><td>{d['submitted_at']}</td><td><span class="badge badge-pending">Pending</span></td><td><a class="btn btn-sm btn-outline" href="/admin/driver/{name}">Open</a></td></tr>""" for i, (name, d) in enumerate(pending_drivers.items(), start=1)])
    live_users = [{"id": uid, "name": user["name"], "role": user["role"], "status": user.get("status", "Active")} for uid, user in users_db.items() if user["role"] in ["Customer", "Vendor", "Driver"]]
    live_users.sort(key=lambda x: (x["role"], x["name"]))
    def role_badge(role): return "badge-customer" if role=="Customer" else "badge-vendor" if role=="Vendor" else "badge-driver"
    live_rows = "".join([f"""<tr><td>{u['id']}</td><td>{u['name']}</td><td><span class="badge {role_badge(u['role'])}">{u['role']}</span></td><td><span class="badge badge-live">{u['status']}</span></td></tr>""" for u in live_users])
    return render_template_string(f"""{COMMON_STYLE}<div class="page"><div class="topbar"><div class="topbar-left"><h1 style="color:var(--le-dark);margin-bottom:4px;">Admin Dashboard</h1><div class="muted">Review vendor and driver applications and manage live users</div></div><a href="/" class="btn btn-secondary">Logout</a></div><div class="stats"><div class="stat-box"><div class="stat-label">Pending Vendors</div><div class="stat-value">{len(pending_vendors)}</div></div><div class="stat-box"><div class="stat-label">Pending Drivers</div><div class="stat-value">{len(pending_drivers)}</div></div><div class="stat-box"><div class="stat-label">Live Vendors</div><div class="stat-value">{sum(1 for u in users_db.values() if u['role']=='Vendor')}</div></div><div class="stat-box"><div class="stat-label">Live Drivers</div><div class="stat-value">{sum(1 for u in users_db.values() if u['role']=='Driver')}</div></div></div>
    <div class="card"><h3>Pending Vendor Applications</h3>{f'<table><thead><tr><th>#</th><th>Name</th><th>Type</th><th>Submitted</th><th>Status</th><th>Action</th></tr></thead><tbody>{pending_vendor_rows}</tbody></table>' if pending_vendor_rows else '<div class="empty-state">No pending vendor applications.</div>'}</div>
    <div class="card"><h3>Pending Driver Applications</h3>{f'<table><thead><tr><th>#</th><th>Name</th><th>Type</th><th>Submitted</th><th>Status</th><th>Action</th></tr></thead><tbody>{pending_driver_rows}</tbody></table>' if pending_driver_rows else '<div class="empty-state">No pending driver applications.</div>'}</div>
    <div class="card"><h3>Current Live Users</h3>{f'<table><thead><tr><th>User ID</th><th>Name</th><th>Type</th><th>Status</th></tr></thead><tbody>{live_rows}</tbody></table>' if live_rows else '<div class="empty-state">No live users found.</div>'}</div></div>""")

@app.route('/admin/vendor/<vname>')
def admin_vendor_detail(vname):
    data = pending_vendors.get(vname)
    if not data: return "<h3>Vendor application not found.</h3><a href='/admin'>Back to Admin</a>"
    file_url, preview_html = url_for('uploaded_file', filename=data["file"]), render_file_preview(data["file"])
    return render_template_string(f"""{COMMON_STYLE}<div class="page"><div class="topbar"><div class="topbar-left"><h1 style="color:var(--le-dark);margin-bottom:4px;">Vendor Application Review</h1><div class="muted">Inspect submitted information and uploaded document</div></div><a href="/admin" class="btn btn-secondary">Back to Dashboard</a></div><div class="grid-2"><div class="card"><h3>Submitted Information</h3><div class="info-list"><div class="info-item"><div class="info-label">Restaurant Name</div><div class="info-value">{data['name']}</div></div><div class="info-item"><div class="info-label">Address</div><div class="info-value">{data['address']}</div></div><div class="info-item"><div class="info-label">Document</div><div class="info-value">{data['file']}</div></div><div class="info-item"><div class="info-label">Status</div><div class="info-value">{data['status']}</div></div><div class="info-item"><div class="info-label">Submitted At</div><div class="info-value">{data['submitted_at']}</div></div></div><div class="actions"><a class="btn" href="/approve/vendor/{vname}">Approve Vendor</a><a class="btn btn-danger" href="/decline_form/vendor/{vname}">Decline Vendor</a><a class="btn btn-outline" href="{file_url}" target="_blank">Open File in New Tab</a></div></div><div class="card"><h3>Document Preview</h3>{preview_html}</div></div></div>""")

@app.route('/admin/driver/<dname>')
def admin_driver_detail(dname):
    data = pending_drivers.get(dname)
    if not data: return "<h3>Driver application not found.</h3><a href='/admin'>Back to Admin</a>"
    license_url, nid_url = url_for('uploaded_file', filename=data["license_file"]), url_for('uploaded_file', filename=data["nid_file"])
    license_preview, nid_preview = render_file_preview(data["license_file"]), render_file_preview(data["nid_file"])
    return render_template_string(f"""{COMMON_STYLE}<div class="page"><div class="topbar"><div class="topbar-left"><h1 style="color:var(--le-dark);margin-bottom:4px;">Driver Application Review</h1><div class="muted">Inspect driver details, vehicle details, and required identity documents</div></div><a href="/admin" class="btn btn-secondary">Back to Dashboard</a></div>
    <div class="card"><h3>Submitted Information</h3><div class="info-list">
    <div class="info-item"><div class="info-label">Driver Name</div><div class="info-value">{data['name']}</div></div>
    <div class="info-item"><div class="info-label">Phone Number</div><div class="info-value">{data['phone']}</div></div>
    <div class="info-item"><div class="info-label">Vehicle Type</div><div class="info-value">{data['vehicle_type']}</div></div>
    <div class="info-item"><div class="info-label">Vehicle Plate Number</div><div class="info-value">{data['vehicle_plate']}</div></div>
    <div class="info-item"><div class="info-label">Bank Account / Mobile Wallet</div><div class="info-value">{data['bank_wallet']}</div></div>
    <div class="info-item"><div class="info-label">Status</div><div class="info-value">{data['status']}</div></div>
    <div class="info-item"><div class="info-label">Submitted At</div><div class="info-value">{data['submitted_at']}</div></div></div>
    <div class="actions"><a class="btn" href="/approve/driver/{dname}">Approve Driver</a><a class="btn btn-danger" href="/decline_form/driver/{dname}">Decline Driver</a></div></div>
    <div class="grid-2"><div class="card"><h3>Driver's License</h3>{license_preview}<div class="actions"><a class="btn btn-outline" href="{license_url}" target="_blank">Open License File</a></div></div><div class="card"><h3>National ID</h3>{nid_preview}<div class="actions"><a class="btn btn-outline" href="{nid_url}" target="_blank">Open National ID File</a></div></div></div></div>""")

@app.route('/decline_form/vendor/<vname>')
def decline_vendor_form(vname):
    if vname not in pending_vendors: return "<h3>Vendor application not found.</h3><a href='/admin'>Back to Admin</a>"
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo" style="color:var(--danger);">Decline Vendor</div><h3>Select a reason</h3><form action="/decline/vendor/{vname}" method="POST"><label>Standardised Reason for Decline</label><select name="reason" required><option value="">Choose a reason</option>{decline_reason_options()}</select><button type="submit" class="btn btn-danger full-width">Confirm Decline</button></form><div style="margin-top:12px;"><a href="/admin/vendor/{vname}" class="btn btn-secondary">Cancel</a></div></div>""")

@app.route('/decline_form/driver/<dname>')
def decline_driver_form(dname):
    if dname not in pending_drivers: return "<h3>Driver application not found.</h3><a href='/admin'>Back to Admin</a>"
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo" style="color:var(--danger);">Decline Driver</div><h3>Select a reason</h3><form action="/decline/driver/{dname}" method="POST"><label>Standardised Reason for Decline</label><select name="reason" required><option value="">Choose a reason</option>{decline_reason_options()}</select><button type="submit" class="btn btn-danger full-width">Confirm Decline</button></form><div style="margin-top:12px;"><a href="/admin/driver/{dname}" class="btn btn-secondary">Cancel</a></div></div>""")

@app.route('/approve/vendor/<vname>')
def approve_vendor(vname):
    data = pending_vendors.get(vname)
    if not data: return "<h3>Vendor application not found.</h3><a href='/admin'>Back to Admin</a>"
    new_id = next_id("VEND"); users_db[new_id] = {"role": "Vendor", "name": data["name"], "status": "Active"}; del pending_vendors[vname]
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">Approved</div><div class="success-box"><h3 style="color:var(--le-dark);">Vendor approved successfully</h3><p><strong>{data['name']}</strong> is now a live vendor.</p><p>New User ID: <strong>{new_id}</strong></p><p>User Type: <strong>Vendor</strong></p></div><div class="actions" style="justify-content:center;"><a href="/admin" class="btn">Back to Admin Dashboard</a></div></div>""")

@app.route('/approve/driver/<dname>')
def approve_driver(dname):
    data = pending_drivers.get(dname)
    if not data: return "<h3>Driver application not found.</h3><a href='/admin'>Back to Admin</a>"
    new_id = next_id("DRV"); users_db[new_id] = {"role": "Driver", "name": data["name"], "status": "Active"}; del pending_drivers[dname]
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">Approved</div><div class="success-box"><h3 style="color:var(--le-dark);">Driver approved successfully</h3><p><strong>{data['name']}</strong> is now a live driver.</p><p>New User ID: <strong>{new_id}</strong></p><p>User Type: <strong>Driver</strong></p></div><div class="actions" style="justify-content:center;"><a href="/admin" class="btn">Back to Admin Dashboard</a></div></div>""")

@app.route('/decline/vendor/<vname>', methods=['POST'])
def decline_vendor(vname):
    data, reason = pending_vendors.get(vname), request.form.get('reason', '').strip()
    if not data: return "<h3>Vendor application not found.</h3><a href='/admin'>Back to Admin</a>"
    if reason not in DECLINE_REASONS: return "<h3>Invalid decline reason.</h3><a href='/admin'>Back to Admin</a>"
    del pending_vendors[vname]
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo" style="color:var(--danger);">Declined</div><div class="danger-box"><h3 style="color:var(--danger);">Vendor application declined</h3><p><strong>{data['name']}</strong> has been removed from pending applications.</p><p><strong>Reason:</strong> {reason}</p><p>No live vendor account was created.</p></div><div class="actions" style="justify-content:center;"><a href="/admin" class="btn btn-secondary">Back to Admin Dashboard</a></div></div>""")

@app.route('/decline/driver/<dname>', methods=['POST'])
def decline_driver(dname):
    data, reason = pending_drivers.get(dname), request.form.get('reason', '').strip()
    if not data: return "<h3>Driver application not found.</h3><a href='/admin'>Back to Admin</a>"
    if reason not in DECLINE_REASONS: return "<h3>Invalid decline reason.</h3><a href='/admin'>Back to Admin</a>"
    del pending_drivers[dname]
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo" style="color:var(--danger);">Declined</div><div class="danger-box"><h3 style="color:var(--danger);">Driver application declined</h3><p><strong>{data['name']}</strong> has been removed from pending applications.</p><p><strong>Reason:</strong> {reason}</p><p>No live driver account was created.</p></div><div class="actions" style="justify-content:center;"><a href="/admin" class="btn btn-secondary">Back to Admin Dashboard</a></div></div>""")

# ─────────────────────────────────────────────
# MENU MANAGEMENT — VENDOR ROUTES
# ─────────────────────────────────────────────

@app.route('/vendor/menu')
def vendor_menu():
    uid = request.args.get('uid', '')
    name = request.args.get('name', 'Vendor')
    # Resolve vendor's restaurant name from users_db
    vendor_info = users_db.get(uid, {})
    restaurant_name = vendor_info.get('name', name)
    active_cat = request.args.get('cat', '')

    menu = get_vendor_menu(restaurant_name)
    categories = menu['categories']
    items = menu['items']

    # Default to first category if none selected
    if not active_cat and categories:
        active_cat = categories[0]

    # Build category sidebar
    cat_links = ""
    for cat in categories:
        active_cls = "active" if cat == active_cat else ""
        cat_links += f'<a class="category-item {active_cls}" href="/vendor/menu?uid={uid}&name={name}&cat={cat}">{cat}</a>'

    # Build items for active category
    items_html = ""
    cat_items = [(iid, item) for iid, item in items.items() if item['category'] == active_cat]
    if cat_items:
        for iid, item in cat_items:
            oos_cls = "out-of-stock-row" if not item['in_stock'] else ""
            stock_badge = '<span class="badge badge-instock">In stock</span>' if item['in_stock'] else '<span class="badge badge-outofstock">Out of stock</span>'
            toggle_label = "Mark Out of Stock" if item['in_stock'] else "Mark In Stock"
            toggle_cls = "btn-warning" if item['in_stock'] else "btn"
            img_html = f'<img src="/uploads/{item["image"]}" class="menu-item-img" alt="{item["name"]}">' if item.get('image') else f'<div class="menu-item-img-placeholder">🍽️</div>'
            desc_html = f'<div class="menu-item-desc">{item["description"]}</div>' if item.get('description') else ''
            items_html += f"""
            <div class="menu-item-row {oos_cls}">
                {img_html}
                <div class="menu-item-info">
                    <div class="menu-item-name">{item['name']}</div>
                    <div class="menu-item-price">{item['price']} EGP</div>
                    {desc_html}
                </div>
                <div class="menu-item-actions">
                    {stock_badge}
                    <a class="btn btn-sm btn-outline" href="/vendor/menu/edit/{iid}?uid={uid}&name={name}&cat={active_cat}">Edit</a>
                    <a class="btn btn-sm {toggle_cls}" href="/vendor/menu/toggle/{iid}?uid={uid}&name={name}&cat={active_cat}">{toggle_label}</a>
                    <a class="btn btn-sm btn-danger" href="/vendor/menu/delete/{iid}?uid={uid}&name={name}&cat={active_cat}" onclick="return confirm('Delete this item?')">Delete</a>
                </div>
            </div>"""
    else:
        items_html = f'<div class="empty-state">No items in this category yet. Add one below.</div>'

    # Add item form (only if there are categories)
    add_item_form = ""
    if categories:
        cat_options = "".join([f'<option value="{c}" {"selected" if c == active_cat else ""}>{c}</option>' for c in categories])
        add_item_form = f"""
        <div class="card">
            <h3>Add New Item{f' to {active_cat}' if active_cat else ''}</h3>
            <form action="/vendor/menu/add_item" method="POST" enctype="multipart/form-data">
                <input type="hidden" name="uid" value="{uid}">
                <input type="hidden" name="name" value="{name}">
                <label>Category</label>
                <select name="category">{cat_options}</select>
                <label>Item Name</label>
                <input type="text" name="item_name" placeholder="e.g. Margherita Pizza" required>
                <label>Price (EGP)</label>
                <input type="number" name="price" placeholder="e.g. 120" min="0" step="0.5" required>
                <label>Description (optional)</label>
                <textarea name="description" rows="2" placeholder="Brief description of the item" style="resize:vertical;"></textarea>
                <label>Item Photo (optional, JPG/PNG)</label>
                <input type="file" name="item_image" accept=".jpg,.jpeg,.png">
                <button type="submit" class="btn" style="margin-top:12px;">Add Item</button>
            </form>
        </div>"""

    # Add category form
    add_cat_form = f"""
    <form action="/vendor/menu/add_category" method="POST" style="display:flex;gap:10px;margin-top:16px;">
        <input type="hidden" name="uid" value="{uid}">
        <input type="hidden" name="name" value="{name}">
        <input type="text" name="category_name" placeholder="New category name" required style="margin:0;flex:1;">
        <button type="submit" class="btn btn-outline">+ Add</button>
    </form>"""

    no_cat_msg = ""
    if not categories:
        no_cat_msg = '<div class="empty-state" style="margin-bottom:20px;">No categories yet. Add your first category to get started.</div>'

    return render_template_string(f"""{COMMON_STYLE}
    <div class="page">
        <div class="topbar">
            <div class="topbar-left">
                <h1 style="color:var(--le-dark);margin-bottom:4px;">Menu Management</h1>
                <div class="muted">{restaurant_name} &nbsp;•&nbsp; User ID: {uid}</div>
            </div>
            <div style="display:flex;gap:10px;">
                <a href="/vendor?uid={uid}&name={name}" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>
        <div class="menu-wrap">
            <div class="menu-sidebar">
                <h3 style="margin-bottom:14px;">Categories</h3>
                {cat_links if cat_links else '<div class="muted" style="font-size:13px;">No categories yet.</div>'}
                {add_cat_form}
            </div>
            <div class="menu-content">
                {no_cat_msg}
                {'<div class="card"><h3>Items in ' + active_cat + '</h3>' + items_html + '</div>' if active_cat else ''}
                {add_item_form}
            </div>
        </div>
    </div>""")

@app.route('/vendor/menu/add_category', methods=['POST'])
def vendor_menu_add_category():
    uid = request.form.get('uid', '')
    name = request.form.get('name', 'Vendor')
    cat_name = request.form.get('category_name', '').strip()
    vendor_info = users_db.get(uid, {})
    restaurant_name = vendor_info.get('name', name)
    if cat_name:
        menu = get_vendor_menu(restaurant_name)
        if cat_name not in menu['categories']:
            menu['categories'].append(cat_name)
    return redirect(url_for('vendor_menu', uid=uid, name=name, cat=cat_name))

@app.route('/vendor/menu/add_item', methods=['POST'])
def vendor_menu_add_item():
    uid = request.form.get('uid', '')
    name = request.form.get('name', 'Vendor')
    category = request.form.get('category', '').strip()
    item_name = request.form.get('item_name', '').strip()
    price = request.form.get('price', '0').strip()
    description = request.form.get('description', '').strip()
    image_file = request.files.get('item_image')
    vendor_info = users_db.get(uid, {})
    restaurant_name = vendor_info.get('name', name)

    if not item_name or not category: return redirect(url_for('vendor_menu', uid=uid, name=name))

    menu = get_vendor_menu(restaurant_name)
    item_id = str(uuid.uuid4())[:8]
    saved_image = None
    if image_file and allowed_file(image_file.filename):
        img_filename = secure_filename(f"menu_{restaurant_name}_{item_id}_{image_file.filename}")
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        saved_image = img_filename

    menu['items'][item_id] = {
        "name": item_name,
        "price": price,
        "description": description,
        "category": category,
        "in_stock": True,
        "image": saved_image
    }
    return redirect(url_for('vendor_menu', uid=uid, name=name, cat=category))

@app.route('/vendor/menu/edit/<item_id>', methods=['GET', 'POST'])
def vendor_menu_edit_item(item_id):
    uid = request.args.get('uid', '') or request.form.get('uid', '')
    name = request.args.get('name', 'Vendor') or request.form.get('name', 'Vendor')
    cat = request.args.get('cat', '') or request.form.get('cat', '')
    vendor_info = users_db.get(uid, {})
    restaurant_name = vendor_info.get('name', name)
    menu = get_vendor_menu(restaurant_name)
    item = menu['items'].get(item_id)
    if not item: return redirect(url_for('vendor_menu', uid=uid, name=name))

    if request.method == 'POST':
        item['name'] = request.form.get('item_name', item['name']).strip()
        item['price'] = request.form.get('price', item['price']).strip()
        item['description'] = request.form.get('description', item.get('description', '')).strip()
        new_cat = request.form.get('category', item['category']).strip()
        item['category'] = new_cat
        image_file = request.files.get('item_image')
        if image_file and allowed_file(image_file.filename):
            img_filename = secure_filename(f"menu_{restaurant_name}_{item_id}_{image_file.filename}")
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
            item['image'] = img_filename
        return redirect(url_for('vendor_menu', uid=uid, name=name, cat=new_cat))

    cat_options = "".join([f'<option value="{c}" {"selected" if c == item["category"] else ""}>{c}</option>' for c in menu['categories']])
    return render_template_string(f"""{COMMON_STYLE}
    <div class="card" style="max-width:560px;margin:40px auto;">
        <h2>Edit Item</h2>
        <form action="/vendor/menu/edit/{item_id}" method="POST" enctype="multipart/form-data">
            <input type="hidden" name="uid" value="{uid}">
            <input type="hidden" name="name" value="{name}">
            <input type="hidden" name="cat" value="{cat}">
            <label>Category</label>
            <select name="category">{cat_options}</select>
            <label>Item Name</label>
            <input type="text" name="item_name" value="{item['name']}" required>
            <label>Price (EGP)</label>
            <input type="number" name="price" value="{item['price']}" min="0" step="0.5" required>
            <label>Description</label>
            <textarea name="description" rows="2" style="resize:vertical;">{item.get('description','')}</textarea>
            <label>Replace Photo (optional)</label>
            <input type="file" name="item_image" accept=".jpg,.jpeg,.png">
            <div style="display:flex;gap:12px;margin-top:14px;">
                <button type="submit" class="btn">Save Changes</button>
                <a href="/vendor/menu?uid={uid}&name={name}&cat={cat}" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>""")

@app.route('/vendor/menu/delete/<item_id>')
def vendor_menu_delete_item(item_id):
    uid = request.args.get('uid', '')
    name = request.args.get('name', 'Vendor')
    cat = request.args.get('cat', '')
    vendor_info = users_db.get(uid, {})
    restaurant_name = vendor_info.get('name', name)
    menu = get_vendor_menu(restaurant_name)
    if item_id in menu['items']:
        del menu['items'][item_id]
    return redirect(url_for('vendor_menu', uid=uid, name=name, cat=cat))

@app.route('/vendor/menu/toggle/<item_id>')
def vendor_menu_toggle_stock(item_id):
    uid = request.args.get('uid', '')
    name = request.args.get('name', 'Vendor')
    cat = request.args.get('cat', '')
    vendor_info = users_db.get(uid, {})
    restaurant_name = vendor_info.get('name', name)
    menu = get_vendor_menu(restaurant_name)
    if item_id in menu['items']:
        menu['items'][item_id]['in_stock'] = not menu['items'][item_id]['in_stock']
    return redirect(url_for('vendor_menu', uid=uid, name=name, cat=cat))

# ─────────────────────────────────────────────
# CUSTOMER ROUTES
# ─────────────────────────────────────────────

@app.route('/customer', methods=['GET', 'POST'])
def customer_dashboard():
    uid, name = request.args.get('uid', 'C303'), request.args.get('name', 'Customer')
    user_lat, user_lon = 30.5, 30.5
    cuisine, rating, fee, time = request.form.get('cuisine'), request.form.get('rating'), request.form.get('fee'), request.form.get('time')
    results = []
    for v in vendors:
        dist = calculate_distance(user_lat, user_lon, v["lat"], v["lon"])
        if dist > 15: continue
        if cuisine and cuisine.lower() not in v["cuisine"].lower(): continue
        if rating and v["rating"] < float(rating): continue
        if fee and v["fee"] > float(fee): continue
        if time and v["time"] > float(time): continue
        results.append((v, round(dist, 2)))
    vendor_html = "".join([f"""<div class="browse-card"><b>{v['name']}</b><br>{v['cuisine']} | ⭐ {v['rating']}<br>🚚 {v['fee']} EGP | ⏱ {v['time']} mins<br>📍 {d} km<form action="/restaurant/{v['name']}"><input type="hidden" name="cuid" value="{uid}"><input type="hidden" name="cname" value="{name}"><button class="btn">View Menu</button></form></div>""" for v, d in results]) or "<p>No vendors found.</p>"
    return render_template_string(f"""{COMMON_STYLE}<div class="page"><div class="topbar"><div class="topbar-left"><h1 style="color:var(--le-dark);margin-bottom:4px;">Welcome, {name}</h1><div class="muted">User ID: {uid} • Browse nearby restaurants</div></div><a href="/" class="btn btn-secondary">Logout</a></div><div class="browse-wrap"><div class="browse-sidebar"><h3>Filters</h3><form method="POST"><input name="cuisine" placeholder="Cuisine" value="{cuisine or ''}"><input type="number" step="0.1" name="rating" placeholder="Min Rating" value="{rating or ''}"><input type="number" min="0" name="fee" placeholder="Max Delivery Fee" value="{fee or ''}"><input type="number" min="0" name="time" placeholder="Max Delivery Time" value="{time or ''}"><button class="btn">Apply Filters</button></form></div><div class="browse-content"><h2>Restaurants</h2>{vendor_html}</div></div></div>""")

@app.route('/restaurant/<rname>')
def restaurant(rname):
    cuid = request.args.get('cuid', '')
    cname = request.args.get('cname', 'Customer')
    menu = get_vendor_menu(rname)
    categories = menu['categories']
    items = menu['items']

    if not categories:
        menu_section = '<div class="empty-state">This restaurant hasn\'t added their menu yet. Check back soon!</div>'
    else:
        menu_section = ""
        for cat in categories:
            cat_items = [(iid, item) for iid, item in items.items() if item['category'] == cat]
            if not cat_items:
                continue
            items_html = ""
            for iid, item in cat_items:
                oos_cls = "oos" if not item['in_stock'] else ""
                oos_label = '<span style="font-size:11px;background:#ffebee;color:#c62828;padding:2px 8px;border-radius:999px;margin-left:6px;">Unavailable</span>' if not item['in_stock'] else ''
                img_html = f'<img src="/uploads/{item["image"]}" class="cust-item-img" alt="{item["name"]}">' if item.get('image') else '<div class="cust-item-img-placeholder">🍽️</div>'
                desc_html = f'<div class="cust-item-desc">{item["description"]}</div>' if item.get('description') else ''
                items_html += f"""
                <div class="cust-item {oos_cls}">
                    {img_html}
                    <div>
                        <div class="cust-item-name">{item['name']}{oos_label}</div>
                        <div class="cust-item-price">{item['price']} EGP</div>
                        {desc_html}
                    </div>
                </div>"""
            menu_section += f'<div class="cust-category"><div class="cust-category-title">{cat}</div>{items_html}</div>'

    back_url = f'/customer?uid={cuid}&name={cname}' if cuid else '/customer'
    return render_template_string(f"""{COMMON_STYLE}
    <div class="page">
        <div class="topbar">
            <div class="topbar-left">
                <h1 style="color:var(--le-dark);margin-bottom:4px;">{rname}</h1>
                <div class="muted">Menu</div>
            </div>
            <a href="{back_url}" class="btn btn-secondary">Back</a>
        </div>
        <div class="browse-content">
            {menu_section}
        </div>
    </div>""")

# ─────────────────────────────────────────────
# VENDOR & DRIVER DASHBOARDS
# ─────────────────────────────────────────────

@app.route('/vendor')
def vendor_dashboard():
    uid, name = request.args.get('uid'), request.args.get('name', 'Vendor')
    vendor_info = users_db.get(uid, {})
    restaurant_name = vendor_info.get('name', name)
    menu = get_vendor_menu(restaurant_name)
    item_count = len(menu['items'])
    cat_count = len(menu['categories'])
    return render_template_string(f"""{COMMON_STYLE}
    <div class="page">
        <div class="topbar">
            <div class="topbar-left">
                <h1 style="color:var(--le-dark);margin-bottom:4px;">Vendor Dashboard</h1>
                <div class="muted">{restaurant_name} &nbsp;•&nbsp; User ID: {uid}</div>
            </div>
            <a href="/" class="btn btn-secondary">Logout</a>
        </div>
        <div class="stats">
            <div class="stat-box"><div class="stat-label">Menu Categories</div><div class="stat-value">{cat_count}</div></div>
            <div class="stat-box"><div class="stat-label">Menu Items</div><div class="stat-value">{item_count}</div></div>
            <div class="stat-box"><div class="stat-label">Status</div><div class="stat-value" style="font-size:18px;color:var(--le-green);">Active</div></div>
        </div>
        <div class="card">
            <h3>Quick Actions</h3>
            <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:8px;">
                <a href="/vendor/menu?uid={uid}&name={name}" class="btn">Manage Menu</a>
            </div>
        </div>
    </div>""")

@app.route('/driver')
def driver_dashboard():
    uid, name = request.args.get('uid'), request.args.get('name', 'Driver')
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">Driver</div><h3>Welcome, {name}</h3><p class="subtitle">User ID: {uid}</p><p>Status: Active for deliveries</p><a href="/" class="btn full-width">Logout</a></div>""")

def open_browser(): webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(port=5000, debug=False)
