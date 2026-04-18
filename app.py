import os, webbrowser
from datetime import datetime
from threading import Timer
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__); app.secret_key = "localeats_final_sprint1"
UPLOAD_FOLDER = 'uploads'; ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}; app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER; os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename): return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def file_extension(filename): return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

users_db = {
    "ADMIN1": {"role": "Admin", "name": "System Admin", "status": "Active"},
    "C303": {"role": "Customer", "name": "Bassant Ibrahim", "status": "Active"}
}
pending_vendors, pending_drivers = {}, {}

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
.info-list{display:grid;gap:14px;} .info-item{background:#fafcfa;border:1px solid var(--border);border-radius:12px;padding:14px;} .info-label{font-size:12px;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.3px;} .info-value{font-size:15px;font-weight:600;word-break:break-word;}
.preview-box{border:1px solid var(--border);border-radius:14px;overflow:hidden;background:#fafafa;min-height:320px;} .preview-frame{width:100%;height:520px;border:none;background:white;} .preview-image{width:100%;max-height:520px;object-fit:contain;display:block;background:white;}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px;} .empty-state{text-align:center;padding:34px 16px;color:var(--muted);border:1px dashed var(--border);border-radius:14px;background:#fcfdfc;}
.success-box{border:2px solid #c8e6c9;background:#f1f8f2;border-radius:12px;padding:18px;margin-top:12px;} .danger-box{border:2px solid #ffcdd2;background:#fff5f5;border-radius:12px;padding:18px;margin-top:12px;}
.choice-card{display:block;padding:18px;border:1px solid var(--border);border-radius:14px;text-decoration:none;color:var(--text);text-align:left;background:#fcfdfc;} .choice-card:hover{background:var(--le-light);}
.section-title{margin:30px 0 12px;}
@media (max-width:900px){.grid-2,.stats{grid-template-columns:1fr;}.topbar{flex-direction:column;align-items:flex-start;} table{font-size:13px;}}
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

def decline_reason_options():
    return "".join([f'<option value="{r}">{r}</option>' for r in DECLINE_REASONS])

@app.route('/')
def login_page():
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">LocalEats</div><h2>Login</h2><p class="subtitle">Sign in with your user ID</p><form action="/auth" method="POST"><input type="text" name="uid" placeholder="Enter ID (Admin: ADMIN1)" required><button type="submit" class="btn full-width">Sign In</button></form><p style="font-size:13px;margin-top:20px;">Want to join LocalEats? <a href="/register" style="color:var(--le-green);text-decoration:none;font-weight:bold;">Register</a></p></div>""")

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
    data = pending_vendors.get(vname)
    if not data: return "<h3>Vendor application not found.</h3><a href='/admin'>Back to Admin</a>"
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo" style="color:var(--danger);">Decline Vendor</div><h3>Select a reason</h3><form action="/decline/vendor/{vname}" method="POST"><label>Standardised Reason for Decline</label><select name="reason" required><option value="">Choose a reason</option>{decline_reason_options()}</select><button type="submit" class="btn btn-danger full-width">Confirm Decline</button></form><div style="margin-top:12px;"><a href="/admin/vendor/{vname}" class="btn btn-secondary">Cancel</a></div></div>""")

@app.route('/decline_form/driver/<dname>')
def decline_driver_form(dname):
    data = pending_drivers.get(dname)
    if not data: return "<h3>Driver application not found.</h3><a href='/admin'>Back to Admin</a>"
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
    data = pending_vendors.get(vname); reason = request.form.get('reason', '').strip()
    if not data: return "<h3>Vendor application not found.</h3><a href='/admin'>Back to Admin</a>"
    if reason not in DECLINE_REASONS: return "<h3>Invalid decline reason.</h3><a href='/admin'>Back to Admin</a>"
    del pending_vendors[vname]
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo" style="color:var(--danger);">Declined</div><div class="danger-box"><h3 style="color:var(--danger);">Vendor application declined</h3><p><strong>{data['name']}</strong> has been removed from pending applications.</p><p><strong>Reason:</strong> {reason}</p><p>No live vendor account was created.</p></div><div class="actions" style="justify-content:center;"><a href="/admin" class="btn btn-secondary">Back to Admin Dashboard</a></div></div>""")

@app.route('/decline/driver/<dname>', methods=['POST'])
def decline_driver(dname):
    data = pending_drivers.get(dname); reason = request.form.get('reason', '').strip()
    if not data: return "<h3>Driver application not found.</h3><a href='/admin'>Back to Admin</a>"
    if reason not in DECLINE_REASONS: return "<h3>Invalid decline reason.</h3><a href='/admin'>Back to Admin</a>"
    del pending_drivers[dname]
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo" style="color:var(--danger);">Declined</div><div class="danger-box"><h3 style="color:var(--danger);">Driver application declined</h3><p><strong>{data['name']}</strong> has been removed from pending applications.</p><p><strong>Reason:</strong> {reason}</p><p>No live driver account was created.</p></div><div class="actions" style="justify-content:center;"><a href="/admin" class="btn btn-secondary">Back to Admin Dashboard</a></div></div>""")

@app.route('/customer')
def customer_dashboard():
    uid, name = request.args.get('uid'), request.args.get('name', 'Customer')
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">Customer</div><h3>Welcome, {name}</h3><p class="subtitle">User ID: {uid}</p><p>Status: Active</p><a href="/" class="btn full-width">Logout</a></div>""")

@app.route('/vendor')
def vendor_dashboard():
    uid, name = request.args.get('uid'), request.args.get('name', 'Vendor')
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">Storefront</div><h3>Welcome, {name}</h3><p class="subtitle">User ID: {uid}</p><p>Status: Verified</p><a href="/" class="btn full-width">Logout</a></div>""")

@app.route('/driver')
def driver_dashboard():
    uid, name = request.args.get('uid'), request.args.get('name', 'Driver')
    return render_template_string(f"""{COMMON_STYLE}<div class="card center-card"><div class="logo">Driver</div><h3>Welcome, {name}</h3><p class="subtitle">User ID: {uid}</p><p>Status: Active for deliveries</p><a href="/" class="btn full-width">Logout</a></div>""")

def open_browser(): webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(port=5000, debug=False)
    