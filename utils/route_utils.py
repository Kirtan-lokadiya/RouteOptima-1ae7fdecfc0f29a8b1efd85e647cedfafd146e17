import math
import pandas as pd
import numpy as np
import folium

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def insert_shop_location(df, store_lat, store_lon):
    shop_data = pd.DataFrame({
        'Shipment ID': ['Shop'],
        'Latitude': [store_lat],
        'Longitude': [store_lon],
        'Delivery Timeslot': ['Shop']
    })
    return pd.concat([shop_data, df], ignore_index=True)

def calculate_distance_matrix_with_shop(df):
    n = len(df)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            lat1, lon1 = df.iloc[i]['Latitude'], df.iloc[i]['Longitude']
            lat2, lon2 = df.iloc[j]['Latitude'], df.iloc[j]['Longitude']
            dist = haversine(lat1, lon1, lat2, lon2)
            dist_matrix[i, j] = dist_matrix[j, i] = dist
    return dist_matrix

def assign_shipments(headers, distance_matrix, vehicles):
    shipments = headers[1:]  # Exclude shop
    assigned = [False] * len(shipments)
    vehicle_assignments = []
    max_4w_distance = 0

    for vehicle in vehicles:
        count = vehicle["count"]
        if count == float('inf'):
            count = len(shipments)
        for _ in range(count):
            current_capacity = 0
            current_distance = 0
            current_shipments = []
            last_location = 0  # Start at shop index 0
            while current_capacity < vehicle["capacity"]:
                min_distance = float('inf')
                next_shipment = -1
                for i in range(len(shipments)):
                    if not assigned[i]:
                        shipment_index = i + 1
                        if distance_matrix[last_location][shipment_index] < min_distance:
                            min_distance = distance_matrix[last_location][shipment_index]
                            next_shipment = i
                if next_shipment == -1:
                    break
                shipment_index = next_shipment + 1
                total_distance = current_distance + min_distance + distance_matrix[shipment_index][0]
                if total_distance <= vehicle["max_radius"]:
                    current_distance += min_distance
                    current_capacity += 1
                    assigned[next_shipment] = True
                    current_shipments.append(shipments[next_shipment])
                    last_location = shipment_index
                else:
                    break
            if current_shipments:
                total_distance = current_distance + distance_matrix[last_location][0]
                trip_time = (total_distance * 5) + (len(current_shipments) * 10)
                capacity_utilization = current_capacity / vehicle["capacity"]
                time_utilization = trip_time / vehicle["max_trip_time"]
                if vehicle["type"] == "4W":
                    if total_distance > max_4w_distance:
                        max_4w_distance = total_distance
                    distance_utilization = total_distance / max_4w_distance if max_4w_distance != 0 else 0
                else:
                    distance_utilization = total_distance / vehicle["max_radius"]
                route = ["Shop"] + current_shipments + ["Shop"]
                if route.count("Shop") > 2:
                    route = ["Shop"] + [x for x in route if x != "Shop"] + ["Shop"]
                route_string = " -> ".join(route)
                shipments_delivered = ", ".join([x for x in current_shipments if x != "Shop"])
                vehicle_assignments.append({
                    "Vehicle Type": vehicle["type"],
                    "Total Shipments": len(current_shipments),
                    "Shipments Delivered": shipments_delivered,
                    "Route": route_string,
                    "MST Distance": round(total_distance, 2),
                    "Trip Time": round(trip_time, 2),
                    "Capacity Utilization": round(capacity_utilization, 2),
                    "Time Utilization": round(time_utilization, 2),
                    "COV_UTI (Distance Utilization)": round(distance_utilization, 2)
                })
    return vehicle_assignments

def generate_map(route, shipments_df):
    m = folium.Map(location=[shipments_df.iloc[0]['Latitude'], shipments_df.iloc[0]['Longitude']], zoom_start=12)
    folium.Marker(
        location=[shipments_df.iloc[0]['Latitude'], shipments_df.iloc[0]['Longitude']],
        popup='Shop',
        icon=folium.Icon(color='red', icon='home')
    ).add_to(m)
    for i, shipment_id in enumerate(route[1:-1], 1):
        shipment = shipments_df[shipments_df['Shipment ID'] == int(shipment_id)].iloc[0]
        folium.Marker(
            location=[shipment['Latitude'], shipment['Longitude']],
            popup=f"Stop {i} (Order {shipment_id})",
            icon=folium.Icon(color='blue', icon='shopping-cart', prefix='fa')
        ).add_to(m)
    route_coords = [[shipments_df.iloc[0]['Latitude'], shipments_df.iloc[0]['Longitude']]]
    for shipment_id in route[1:-1]:
        shipment = shipments_df[shipments_df['Shipment ID'] == int(shipment_id)].iloc[0]
        route_coords.append([shipment['Latitude'], shipment['Longitude']])
    route_coords.append([shipments_df.iloc[0]['Latitude'], shipments_df.iloc[0]['Longitude']])
    folium.PolyLine(
        locations=route_coords,
        weight=5,
        color='blue',
        opacity=0.8,
        tooltip='Route'
    ).add_to(m)
    return m._repr_html_()
