# routes/optimization.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import pandas as pd
from utils.route_utils import (
    insert_shop_location,
    calculate_distance_matrix_with_shop,
    assign_shipments,
    generate_map
)

# Import our custom login_required decorator
from decorators import login_required
from decorators import token_required

optimization_bp = Blueprint('optimization', __name__)

# In-memory cache (for production, consider a persistent cache)
cache = {
    'excel_data': None,
    'assignments': {}
}

@optimization_bp.route('/')
#@login_required
# @token_required
def home():
    current_app.logger.info("Home page accessed")
    return render_template('index.html')

@optimization_bp.route('/upload', methods=['GET', 'POST'])
#@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            try:
                cache['excel_data'] = pd.read_excel(file, sheet_name="Shipments_Data")
                current_app.logger.info("Excel file loaded successfully")
            except Exception as e:
                current_app.logger.error("Error reading Excel file: %s", e)
                return redirect(request.url)
            return redirect(url_for('optimization.select_timeslot'))
    return render_template('upload.html')

@optimization_bp.route('/select_timeslot', methods=['GET', 'POST'])
#@login_required
def select_timeslot():
    if request.method == 'POST':
        timeslot = request.form['timeslot']
        return redirect(url_for('optimization.show_trips', timeslot=timeslot))
    return render_template('select_timeslot.html')

@optimization_bp.route('/trips/<timeslot>')
#@login_required
def show_trips(timeslot):
    shipments_df = cache.get('excel_data')
    if shipments_df is None:
        return redirect(url_for('optimization.upload_file'))
    store_lat, store_lon = shipments_df.iloc[0]['Latitude'], shipments_df.iloc[0]['Longitude']
    df_timeslot = shipments_df[shipments_df['Delivery Timeslot'] == timeslot]
    df_timeslot_with_shop = insert_shop_location(df_timeslot, store_lat, store_lon)
    dist_matrix = calculate_distance_matrix_with_shop(df_timeslot_with_shop)
    headers = ['Shop'] + df_timeslot['Shipment ID'].astype(str).tolist()

    vehicles = [
        {"type": "3W", "count": 50, "capacity": 5, "max_radius": 15, "max_trip_time": 240},
        {"type": "4W-EV", "count": 25, "capacity": 8, "max_radius": 20, "max_trip_time": 300},
        {"type": "4W", "count": float('inf'), "capacity": 25, "max_radius": float('inf'), "max_trip_time": 480}
    ]
    assignments = assign_shipments(headers, dist_matrix.tolist(), vehicles)
    cache['assignments'][timeslot] = assignments
    current_app.logger.info("Trip assignments calculated for timeslot: %s", timeslot)
    return render_template('trips.html', assignments=assignments, timeslot=timeslot)

@optimization_bp.route('/map/<timeslot>/<int:index>')
#@login_required
def show_map(timeslot, index):
    shipments_df = cache.get('excel_data')
    assignments = cache.get('assignments', {}).get(timeslot, [])
    if shipments_df is None or not assignments:
        return redirect(url_for('optimization.upload_file'))
    route = assignments[index]['Route'].split(' -> ')
    map_html = generate_map(route, shipments_df)
    return render_template('map.html', map_html=map_html, timeslot=timeslot)

@optimization_bp.route('/open_maps/<timeslot>/<int:index>')
#@login_required
def open_maps(timeslot, index):
    shipments_df = cache.get('excel_data')
    assignments = cache.get('assignments', {}).get(timeslot, [])
    if shipments_df is None or not assignments:
        return redirect(url_for('optimization.upload_file'))
    
    route = assignments[index]['Route'].split(' -> ')
    # Get coordinates for the route
    coordinates = []
    
    for stop in route:
        if stop == 'Shop':
            # Use first row coordinates as shop location
            lat, lon = shipments_df.iloc[0]['Latitude'], shipments_df.iloc[0]['Longitude']
        else:
            # Find shipment coordinates
            shipment = shipments_df[shipments_df['Shipment ID'] == int(stop)]
            if not shipment.empty:
                lat, lon = shipment.iloc[0]['Latitude'], shipment.iloc[0]['Longitude']
            else:
                continue
        coordinates.append(f"{lat},{lon}")
    
    # Create Google Maps URL with waypoints
    if len(coordinates) >= 2:
        # Remove duplicate shop coordinates if route starts and ends at shop
        if coordinates[0] == coordinates[-1] and len(coordinates) > 2:
            coordinates = coordinates[:-1]  # Remove last shop
        
        origin = coordinates[0]
        destination = coordinates[-1]
        
        if len(coordinates) > 2:
            waypoints = "|".join(coordinates[1:-1])
            maps_url = f"https://www.google.com/maps/dir/{origin}/{destination}?waypoints={waypoints}"
        else:
            maps_url = f"https://www.google.com/maps/dir/{origin}/{destination}"
        
        return redirect(maps_url)
    
    return redirect(url_for('optimization.show_trips', timeslot=timeslot))

@optimization_bp.route('/get_directions/<timeslot>/<int:index>')
#@login_required
def get_directions(timeslot, index):
    shipments_df = cache.get('excel_data')
    assignments = cache.get('assignments', {}).get(timeslot, [])
    if shipments_df is None or not assignments:
        return redirect(url_for('optimization.upload_file'))
    
    route = assignments[index]['Route'].split(' -> ')
    # Get coordinates for the route
    coordinates = []
    
    for stop in route:
        if stop == 'Shop':
            # Use first row coordinates as shop location
            lat, lon = shipments_df.iloc[0]['Latitude'], shipments_df.iloc[0]['Longitude']
        else:
            # Find shipment coordinates
            shipment = shipments_df[shipments_df['Shipment ID'] == int(stop)]
            if not shipment.empty:
                lat, lon = shipment.iloc[0]['Latitude'], shipment.iloc[0]['Longitude']
            else:
                continue
        coordinates.append(f"{lat},{lon}")
    
    # Create Google Maps directions URL
    if len(coordinates) >= 2:
        # Remove duplicate shop coordinates if route starts and ends at shop
        if coordinates[0] == coordinates[-1] and len(coordinates) > 2:
            coordinates = coordinates[:-1]  # Remove last shop
        
        origin = coordinates[0]
        destination = coordinates[-1]
        
        if len(coordinates) > 2:
            waypoints = "|".join(coordinates[1:-1])
            directions_url = f"https://www.google.com/maps/dir/{origin}/{destination}?waypoints={waypoints}&travelmode=driving"
        else:
            directions_url = f"https://www.google.com/maps/dir/{origin}/{destination}?travelmode=driving"
        
        return redirect(directions_url)
    
    return redirect(url_for('optimization.show_trips', timeslot=timeslot))
