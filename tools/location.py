import math

# Given data
latitude_deg = 34 + (8 + 0.08333) / 60  # Convert latitude in degrees and minutes
longitude1_deg = 77 + 52 / 60  # First longitude
longitude2_deg = 77 + (51 + 99763 / 100000) / 60  # Second longitude

# Earth's radius in kilometers
R = 6371.0

# Calculate the difference in longitude
delta_longitude_deg = abs(longitude1_deg - longitude2_deg)

# Convert latitude to radians
latitude_rad = math.radians(latitude_deg)

# Calculate the distance
distance_km = delta_longitude_deg * (math.pi / 180) * R * math.cos(latitude_rad)
print(f"Distance: {distance_km} km")
