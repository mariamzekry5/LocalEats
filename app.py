import math
import webbrowser
from threading import Timer
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# ---------------- STYLE ----------------
COMMON_STYLE = """
<style>
body { font-family: Arial; margin:0; display:flex; background:#f4f7f6; }

.sidebar {
    width: 260px;
    background: white;
    padding: 20px;
    height: 100vh;
    box-shadow: 2px 0 10px rgba(0,0,0,0.05);
}

.content {
    flex: 1;
    padding: 20px;
}

.card {
    background: white;
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.btn {
    background: #4CAF50;
    color: white;
    border: none;
    padding: 10px;
    width: 100%;
    margin-top: 10px;
    border-radius: 6px;
    cursor: pointer;
}

input {
    width: 100%;
    padding: 8px;
    margin: 6px 0;
    border-radius: 6px;
    border: 1px solid #ddd;
}
</style>
"""

# ---------------- MOCK DATA ----------------
users_db = {
    "V1": {"role":"Vendor","name":"Pizza House","lat":30.501,"lon":30.502,"cuisine":"Italian","rating":4.5,"fee":20,"time":30},
    "V2": {"role":"Vendor","name":"Koshary beity","lat":30.6,"lon":30.4,"cuisine":"Egyptian","rating":4.8,"fee":10,"time":20},
    "V3": {"role":"Vendor","name":"Burger Zone","lat":31.2,"lon":29.9,"cuisine":"American","rating":3.9,"fee":25,"time":40}
}

# ---------------- DISTANCE ----------------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/browse')

# ---------------- RESTAURANT PAGE ----------------
@app.route('/restaurant/<name>')
def restaurant(name):
    return f"""
    {COMMON_STYLE}
    <div class="content">
        <div class="card">
            <h2>{name}</h2>
            <p>Restaurant page 🍽</p>
            <p>Here we will later show menu...etc.</p>

            <a href="/browse">
                <button class="btn">Back</button>
            </a>
        </div>
    </div>
    """

# ---------------- BROWSE ----------------
@app.route('/browse', methods=['GET', 'POST'])
def browse():

    user_lat = 30.5
    user_lon = 30.5

    cuisine_filter = request.form.get('cuisine')
    rating_filter = request.form.get('rating')
    fee_filter = request.form.get('fee')
    time_filter = request.form.get('time')

    # validation
    if fee_filter and float(fee_filter) < 0:
        return "<h3>Fee cannot be negative</h3><a href='/browse'>Back</a>"

    if time_filter and float(time_filter) < 0:
        return "<h3>Time cannot be negative</h3><a href='/browse'>Back</a>"

    results = []

    for v in users_db.values():
        if v["role"] != "Vendor":
            continue

        dist = calculate_distance(user_lat, user_lon, v["lat"], v["lon"])

        if dist > 15:
            continue

        if cuisine_filter and cuisine_filter.lower() not in v["cuisine"].lower():
            continue

        if rating_filter and v["rating"] < float(rating_filter):
            continue

        if fee_filter and v["fee"] > float(fee_filter):
            continue

        if time_filter and v["time"] > float(time_filter):
            continue

        results.append((v, round(dist, 2)))

    # ---------------- DISPLAY ----------------
    vendor_html = ""

    for v, d in results:
        vendor_html += f"""
        <div class="card">
            <b>{v['name']}</b><br>
            {v['cuisine']} | ⭐ {v['rating']}<br>
            🚚 {v['fee']} EGP | ⏱ {v['time']} mins<br>
            📍 {d} km

            <form action="/restaurant/{v['name']}" method="GET">
                <button class="btn">Select Restaurant</button>
            </form>
        </div>
        """

    if not vendor_html:
        vendor_html = "<p>No vendors found.</p>"

    return f"""
    {COMMON_STYLE}

    <div class="sidebar">
        <h3>Filters</h3>

        <form method="POST">
            <input type="text" name="cuisine" placeholder="Cuisine">
            <input type="number" step="0.1" name="rating" placeholder="Min Rating">

            <input type="number" name="fee" min="0" placeholder="Max Delivery Fee(EGP)">
            <input type="number" name="time" min="0" step="1" placeholder="Maximum Delivery Time">

            <button class="btn">Apply Filters</button>
        </form>
    </div>

    <div class="content">
        <h2>Restaurants</h2>
        {vendor_html}
    </div>
    """

# ---------------- RUN ----------------
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=False)