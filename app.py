import os
import webbrowser
from threading import Timer
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "localeats_final_sprint1"

# --- CONFIG ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- MOCK DATABASE ---
users_db = {
    "ADMIN1": {"role": "Admin", "name": "System Admin"},
    "C303": {"role": "Customer", "name": "Bassant Ibrahim"}
}
pending_vendors = {} 

# --- STYLES ---
COMMON_STYLE = """
<style>
    :root { --le-green: #4CAF50; --le-dark: #2e7d32; --bg: #f4f7f6; }
    body { font-family: 'Segoe UI', sans-serif; background: var(--bg); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); width: 100%; max-width: 450px; text-align: center;}
    .logo { color: var(--le-green); font-weight: bold; font-size: 32px; margin-bottom: 10px; }
    .btn { background: var(--le-green); color: white; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; margin-top: 10px; text-decoration: none; display: inline-block; box-sizing: border-box; font-size: 14px;}
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
    .progress-container { display: flex; justify-content: space-between; margin: 20px 0 40px; position: relative; }
    .progress-line { position: absolute; top: 15px; left: 0; height: 2px; background: #ddd; width: 100%; z-index: 1; }
    .step { width: 30px; height: 30px; border-radius: 50%; background: #ddd; z-index: 2; display: flex; align-items: center; justify-content: center; font-size: 12px; color: white; font-weight: bold; position: relative; }
    .step.active { background: var(--le-green); }
    .step-label { position: absolute; top: 35px; font-size: 10px; color: #888; text-transform: uppercase; white-space: nowrap; }
</style>
"""

# --- ROUTES ---

@app.route('/')
def login_page():
    return render_template_string(f"""
    {COMMON_STYLE}
    <div class="card">
        <div class="logo">LocalEats</div>
        <h2>Login</h2>
        <form action="/auth" method="POST">
            <input type="text" name="uid" placeholder="Enter ID (Admin: ADMIN1)" required>
            <button type="submit" class="btn">Sign In</button>
        </form>
        <p style="font-size: 13px; margin-top: 20px;">Partner with us? <a href="/register" style="color:var(--le-green); text-decoration:none; font-weight:bold;">Register</a></p>
    </div>
    """)

@app.route('/auth', methods=['POST'])
def auth():
    uid = request.form.get('uid').upper()
    if uid in users_db:
        return redirect(url_for(f"{users_db[uid]['role'].lower()}_dashboard", name=users_db[uid]['name']))
    return "<h3>ID Pending or Invalid.</h3><a href='/'>Back</a>"

@app.route('/register')
def register():
    return render_template_string(f"""
    {COMMON_STYLE}
    <div class="card">
        <div class="logo">LocalEats</div>
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="step active">1<span class="step-label" style="left:0">Apply</span></div>
            <div class="step">2<span class="step-label" style="left:-10px">Review</span></div>
            <div class="step">3<span class="step-label" style="right:0">Live</span></div>
        </div>
        <form action="/submit_app" method="POST" enctype="multipart/form-data">
            <input type="text" name="vname" placeholder="Restaurant Name" required>
            <input type="text" name="vaddress" placeholder="Address" required>
            <label style="font-size:11px; color:#666; display:block; text-align:left;">Upload Hygiene Doc (PDF/JPG):</label>
            <input type="file" name="vdoc" accept=".pdf,.jpg,.png,.jpeg" required>
            <button type="submit" class="btn">Submit Application</button>
        </form>
    </div>
    """)

@app.route('/submit_app', methods=['POST'])
def submit_app():
    vname = request.form.get('vname')
    file = request.files.get('vdoc')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{vname}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Save to pending list for Admin to see
        pending_vendors[vname] = {"name": vname, "file": filename}
        
        return render_template_string(f"""
        {COMMON_STYLE}
        <div class="card">
            <div class="logo">LocalEats</div>
            <div style="border: 2px dashed orange; padding: 20px; border-radius: 10px; background: #fffdf5;">
                <h3 style="color:orange;">Application Pending</h3>
                <p>Documents for <strong>{vname}</strong> are being reviewed.</p>
                <p style="font-size:12px;">The file <b>{filename}</b> was successfully uploaded.</p>
            </div>
            <a href="/" class="btn">Return Home</a>
        </div>
        """)
    return "Invalid File Type."

@app.route('/admin')
def admin_dashboard():
    rows = ""
    for vname, data in pending_vendors.items():
        rows += f"<li>{vname} (Doc: {data['file']}) <a href='/approve/{vname}' style='color:blue;'>[Approve]</a></li>"
    
    return render_template_string(f"""
    {COMMON_STYLE}
    <div class="card">
        <div class="logo">Admin</div>
        <h3>Pending Vendors</h3>
        <ul style="text-align:left;">{rows if rows else "No applications."}</ul>
        <a href="/" class="btn" style="background:#666">Logout</a>
    </div>
    """)

@app.route('/approve/<vname>')
def approve(vname):
    new_id = f"VEND{100 + len(users_db)}"
    users_db[new_id] = {"role": "Vendor", "name": vname}
    del pending_vendors[vname]
    return f"<h1>Approved!</h1><p>{vname} ID is: <b>{new_id}</b></p><a href='/admin'>Back to Admin</a>"

@app.route('/vendor')
def vendor_dashboard():
    name = request.args.get('name')
    return render_template_string(f"{COMMON_STYLE}<div class='card'><div class='logo'>Storefront</div><h3>Welcome, {name}</h3><p>Status: Verified</p><a href='/' class='btn'>Logout</a></div>")

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(port=5000, debug=False)