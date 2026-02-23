def format_truck_matches(loads: list) -> str:
    if not loads:
        return "No matching loads found yet. We will notify you when one appears."
    
    msg = "🚛 Matching Loads Found:\n\n"
    for i, load in enumerate(loads, start=1):
        date_str = load.deadline.strftime("%d-%m-%Y")
        msg += f"{i}️⃣ {load.weight} tons\n   {load.pickup_city} → {load.drop_city}\n   Pickup: {date_str}\n\n"
    msg += "Reply: BOOK <number> to reserve."
    return msg

def format_load_matches(trucks: list) -> str:
    if not trucks:
        return "No matching trucks found yet. We will notify you when one appears."
    
    msg = "🚛 Matching Trucks Found:\n\n"
    for i, truck in enumerate(trucks, start=1):
        date_str = truck.departure_time.strftime("%d-%m-%Y")
        msg += f"{i}️⃣ {truck.capacity_available} tons available\n   {truck.source_city} → {truck.destination_city}\n   Departure: {date_str}\n\n"
    msg += "Reply: BOOK <number> to reserve."
    return msg
