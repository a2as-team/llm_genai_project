

"""
Booking validation tool for restaurant reservations.

This tool validates and creates reservations using a greedy algorithm
to find available tables based on capacity, location, and time constraints.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import UUID
from typing import Optional

from src.bdd.dbmanager import DBManager
from src.models.booking import BookingRequest, BookingResponse, TableInfo, AlternativeSlot

# Timezone du restaurant (Paris)
RESTAURANT_TZ = ZoneInfo("Europe/Paris")


def parse_datetime_string(dt_str: str) -> datetime:
    """
    Parse various datetime string formats into a datetime object.
    
    Supported formats:
    - ISO 8601: '2025-12-15T20:00:00', '2025-12-15T20:00'
    - Space separated: '2025-12-15 20:00:00', '2025-12-15 20:00'
    - French format: '15/12/2025 20:00', '15/12/2025 20h00'
    """
    dt_str = dt_str.strip()
    
    # Replace common french hour separator
    dt_str = dt_str.replace('h', ':')
    
    # List of formats to try
    formats = [
        '%Y-%m-%dT%H:%M:%S',      # ISO with seconds
        '%Y-%m-%dT%H:%M',          # ISO without seconds
        '%Y-%m-%d %H:%M:%S',       # Space with seconds
        '%Y-%m-%d %H:%M',          # Space without seconds
        '%d/%m/%Y %H:%M:%S',       # French with seconds
        '%d/%m/%Y %H:%M',          # French without seconds
        '%d-%m-%Y %H:%M:%S',       # French dash with seconds
        '%d-%m-%Y %H:%M',          # French dash without seconds
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    # If all formats fail, raise an error
    raise ValueError(
        f"Format de date non reconnu: '{dt_str}'. "
        "Formats acceptés: '2025-12-15T20:00', '2025-12-15 20:00', '15/12/2025 20:00', '15/12/2025 20h00'"
    )


def parse_hour(hour_str: str) -> tuple[int, int]:
    """Parse hour string like '11h30' or '23h00' into (hour, minute)."""
    hour_str = hour_str.lower().replace("h", ":")
    if ":" in hour_str:
        parts = hour_str.split(":")
        return int(parts[0]), int(parts[1]) if parts[1] else 0
    return int(hour_str), 0


def is_within_service_hours(dt: datetime, hours: dict) -> bool:
    """Check if a datetime falls within lunch or dinner service hours."""
    time_minutes = dt.hour * 60 + dt.minute
    
    # Parse lunch hours
    lunch_open_h, lunch_open_m = parse_hour(hours["lunch_open"])
    lunch_close_h, lunch_close_m = parse_hour(hours["lunch_close"])
    lunch_open = lunch_open_h * 60 + lunch_open_m
    lunch_close = lunch_close_h * 60 + lunch_close_m
    
    # Parse dinner hours
    dinner_open_h, dinner_open_m = parse_hour(hours["dinner_open"])
    dinner_close_h, dinner_close_m = parse_hour(hours["dinner_close"])
    dinner_open = dinner_open_h * 60 + dinner_open_m
    dinner_close = dinner_close_h * 60 + dinner_close_m
    
    return (lunch_open <= time_minutes <= lunch_close) or (dinner_open <= time_minutes <= dinner_close)


def get_service_slots_for_date(date: datetime, hours: dict, slot_minutes: int) -> list[datetime]:
    """Generate all valid time slots for a given date based on service hours."""
    slots = []
    base_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Lunch slots
    lunch_open_h, lunch_open_m = parse_hour(hours["lunch_open"])
    lunch_close_h, lunch_close_m = parse_hour(hours["lunch_close"])
    current = base_date.replace(hour=lunch_open_h, minute=lunch_open_m)
    lunch_end = base_date.replace(hour=lunch_close_h, minute=lunch_close_m)
    
    while current <= lunch_end:
        slots.append(current)
        current += timedelta(minutes=slot_minutes)
    
    # Dinner slots
    dinner_open_h, dinner_open_m = parse_hour(hours["dinner_open"])
    dinner_close_h, dinner_close_m = parse_hour(hours["dinner_close"])
    current = base_date.replace(hour=dinner_open_h, minute=dinner_open_m)
    dinner_end = base_date.replace(hour=dinner_close_h, minute=dinner_close_m)
    
    while current <= dinner_end:
        slots.append(current)
        current += timedelta(minutes=slot_minutes)
    
    return slots


def tables_overlap(
    requested_dt: datetime,
    duration_minutes: int,
    buffer_minutes: int,
    existing_reservations: list[dict],
    table_id: UUID
) -> bool:
    """Check if a table is occupied during the requested time window."""
    # Convert requested_dt to Paris time, then make naive for comparison
    if requested_dt.tzinfo:
        new_start = requested_dt.astimezone(RESTAURANT_TZ).replace(tzinfo=None)
    else:
        new_start = requested_dt
    new_end = new_start + timedelta(minutes=duration_minutes + buffer_minutes)
    
    for res in existing_reservations:
        if table_id not in res["table_ids"]:
            continue
        
        res_start = res["reservation_datetime"]
        # Convert DB datetime (UTC) to Paris time, then make naive
        if res_start.tzinfo:
            res_start = res_start.astimezone(RESTAURANT_TZ).replace(tzinfo=None)
        res_end = res_start + timedelta(minutes=duration_minutes + buffer_minutes)
        
        # Check overlap
        if new_start < res_end and new_end > res_start:
            return True
    
    return False


def find_available_tables(
    tables: list[dict],
    combinations: list[tuple],
    reservations: list[dict],
    requested_dt: datetime,
    num_guests: int,
    duration_minutes: int,
    buffer_minutes: int
) -> Optional[list[dict]]:
    """
    Greedy algorithm to find available tables for a reservation.
    
    Strategy:
    1. Try to find a single table with enough capacity
    2. If not found, try to combine tables
    
    Returns list of tables if found, None otherwise.
    """
    # Filter tables that are not occupied at this time
    available_tables = [
        t for t in tables
        if not tables_overlap(requested_dt, duration_minutes, buffer_minutes, reservations, t["id"])
    ]
    
    if not available_tables:
        return None
    
    # Strategy 1: Find single table with enough capacity (pick smallest that fits)
    for table in sorted(available_tables, key=lambda x: x["capacity"]):
        if table["capacity"] >= num_guests:
            return [table]
    
    # Strategy 2: Try combining tables
    # Build a map of combinable tables
    combo_map = {}
    for t1_id, t2_id in combinations:
        if t1_id not in combo_map:
            combo_map[t1_id] = []
        combo_map[t1_id].append(t2_id)
        if t2_id not in combo_map:
            combo_map[t2_id] = []
        combo_map[t2_id].append(t1_id)
    
    available_ids = {t["id"] for t in available_tables}
    available_by_id = {t["id"]: t for t in available_tables}
    
    # Try pairs of combinable tables
    for table in available_tables:
        if table["id"] in combo_map:
            for partner_id in combo_map[table["id"]]:
                if partner_id in available_ids:
                    combined_capacity = table["capacity"] + available_by_id[partner_id]["capacity"]
                    if combined_capacity >= num_guests:
                        return [table, available_by_id[partner_id]]
    
    return None


async def validate_booking(booking: BookingRequest) -> BookingResponse:
    """
    Validates and creates a restaurant reservation.
    
    This tool receives booking information from the agent and:
    1. Validates the requested time is within service hours
    2. Runs a greedy algorithm to find available tables
    3. If available: creates the reservation and returns success
    4. If not available: returns up to 3 alternative time slots
    
    Parameters:
    - booking: BookingRequest with datetime, guests, location, customer info
    
    Returns:
    - BookingResponse with success status, message, and alternatives if needed
    """
    db_manager = DBManager()
    
    try:
        # 0. Parse datetime string and normalize to Paris timezone
        try:
            reservation_dt = parse_datetime_string(booking.reservation_datetime)
        except ValueError as e:
            return BookingResponse(
                success=False,
                message=str(e)
            )
        
        # Assume parsed datetime is Paris time
        reservation_dt = reservation_dt.replace(tzinfo=RESTAURANT_TZ)
        
        # 1. Get restaurant settings and hours
        settings = await db_manager.get_restaurant_settings()
        hours = await db_manager.get_restaurant_hours()
        
        duration = settings["average_duration_minutes"]
        buffer = settings["buffer_time_minutes"]
        slot_interval = settings["reservation_time_slot"]
        
        # 2. Validate requested time is within service hours
        if not is_within_service_hours(reservation_dt, hours):
            return BookingResponse(
                success=False,
                message=f"L'horaire demandé ({reservation_dt.strftime('%Hh%M')}) n'est pas dans les heures de service. "
                        f"Service midi: {hours['lunch_open']}-{hours['lunch_close']}, "
                        f"Service soir: {hours['dinner_open']}-{hours['dinner_close']}."
            )
        
        # 3. Get tables for requested location
        tables = await db_manager.get_tables_by_location(booking.location)
        
        if not tables:
            # No tables for this location, try the other one
            other_location = "indoor" if booking.location == "outdoor" else "outdoor"
            return BookingResponse(
                success=False,
                message=f"Aucune table disponible en {booking.location}. "
                        f"Souhaitez-vous réserver en {other_location} à la place?"
            )
        
        # 4. Get existing reservations for this date
        reservations = await db_manager.get_reservations_for_date(reservation_dt)
        
        # 5. Get table combinations
        combinations = await db_manager.get_table_combinations()
        
        # 6. Try to find available tables
        available = find_available_tables(
            tables=tables,
            combinations=combinations,
            reservations=reservations,
            requested_dt=reservation_dt,
            num_guests=booking.number_of_guests,
            duration_minutes=duration,
            buffer_minutes=buffer
        )
        
        if available:
            # SUCCESS - Create reservation
            table_ids = [t["id"] for t in available]
            reservation_id = await db_manager.save_reservation(
                customer_name=booking.customer_name,
                customer_phone=booking.customer_phone,
                reservation_datetime=reservation_dt,
                number_of_guests=booking.number_of_guests,
                table_ids=table_ids,
                extra_infos=booking.extra_infos
            )
            
            assigned_tables = [
                TableInfo(id=t["id"], name=t["name"], capacity=t["capacity"], location=t["location"])
                for t in available
            ]
            
            total_capacity = sum(t["capacity"] for t in available)
            table_names = ", ".join(t["name"] for t in available)
            
            return BookingResponse(
                success=True,
                message=f"Réservation confirmée pour {booking.number_of_guests} personnes "
                        f"le {reservation_dt.strftime('%d/%m/%Y à %Hh%M')} "
                        f"en {booking.location}. Tables assignées: {table_names}.",
                reservation_id=UUID(reservation_id),
                assigned_tables=assigned_tables
            )
        
        # FAILURE - Find alternatives
        alternatives = []
        
        # 7a. Find alternative slots at same location (3 closest)
        all_slots = get_service_slots_for_date(reservation_dt, hours, slot_interval)
        
        # Sort slots by distance from requested time
        requested_minutes = reservation_dt.hour * 60 + reservation_dt.minute
        sorted_slots = sorted(
            all_slots,
            key=lambda s: abs((s.hour * 60 + s.minute) - requested_minutes)
        )
        
        for slot in sorted_slots:
            if slot == reservation_dt.replace(tzinfo=None):
                continue  # Skip the already-tried slot
            
            # Add timezone to slot for comparison
            slot_with_tz = slot.replace(tzinfo=RESTAURANT_TZ)
            
            available_alt = find_available_tables(
                tables=tables,
                combinations=combinations,
                reservations=reservations,
                requested_dt=slot_with_tz,
                num_guests=booking.number_of_guests,
                duration_minutes=duration,
                buffer_minutes=buffer
            )
            
            if available_alt:
                alternatives.append(AlternativeSlot(
                    datetime=slot_with_tz,
                    location=booking.location,
                    tables=[TableInfo(id=t["id"], name=t["name"], capacity=t["capacity"], location=t["location"]) for t in available_alt],
                    total_capacity=sum(t["capacity"] for t in available_alt)
                ))
                
                if len(alternatives) >= 3:
                    break
        
        # 7b. If outdoor was requested and few alternatives found, try indoor at same time
        if booking.location == "outdoor" and len(alternatives) < 3:
            indoor_tables = await db_manager.get_tables_by_location("indoor")
            
            if indoor_tables:
                available_indoor = find_available_tables(
                    tables=indoor_tables,
                    combinations=combinations,
                    reservations=reservations,
                    requested_dt=reservation_dt,
                    num_guests=booking.number_of_guests,
                    duration_minutes=duration,
                    buffer_minutes=buffer
                )
                
                if available_indoor:
                    alternatives.insert(0, AlternativeSlot(
                        datetime=reservation_dt,
                        location="indoor",
                        tables=[TableInfo(id=t["id"], name=t["name"], capacity=t["capacity"], location=t["location"]) for t in available_indoor],
                        total_capacity=sum(t["capacity"] for t in available_indoor)
                    ))
        
        if alternatives:
            alt_msgs = []
            for alt in alternatives[:3]:
                alt_msgs.append(f"- {alt.datetime.strftime('%Hh%M')} en {alt.location}")
            
            return BookingResponse(
                success=False,
                message=f"Pas de disponibilité pour {booking.number_of_guests} personnes "
                        f"le {reservation_dt.strftime('%d/%m/%Y à %Hh%M')} en {booking.location}. "
                        f"Alternatives disponibles:\n" + "\n".join(alt_msgs),
                alternatives=alternatives[:3]
            )
        
        return BookingResponse(
            success=False,
            message=f"Désolé, aucune table disponible pour {booking.number_of_guests} personnes "
                    f"le {reservation_dt.strftime('%d/%m/%Y')}. "
                    "Veuillez essayer une autre date."
        )
        
    except Exception as e:
        print(f"[validate_booking] Exception: {e}")
        return BookingResponse(
            success=False,
            message=f"Erreur lors de la validation de la réservation: {str(e)}"
        )

