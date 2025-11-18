from models import GetTableAvailabilityRequest
from .optimizeTableAssignment import optimize_table_assignment
from .findClosestAvailableTime import find_closest_available_time

def check_table_availability(
    request: GetTableAvailabilityRequest,
    tables,
    existing_reservations,
    avg_duration_minutes,
    buffer_time_minutes,
):
    # 1. Essayer l’horaire demandé
    assigned = optimize_table_assignment(
        tables,
        existing_reservations,
        request.reservationDatetime,
        avg_duration_minutes,
        request.numberOfPeople
    )

    if assigned:
        return {
            "isPossible": True,
            "requestedDatetime": request.reservationDatetime,
            "assignedTables": assigned,
            "suggestedDatetime": None,
            "suggestedTables": None,
        }

    # 2. Sinon → chercher l’horaire faisable le plus proche
    closest_datetime, closest_tables = find_closest_available_time(
        tables,
        existing_reservations,
        request.reservationDatetime,
        avg_duration_minutes,
        request.numberOfPeople,
        buffer_time_minutes,
    )

    if closest_datetime is None:
        return {
            "isPossible": False,
            "requestedDatetime": request.reservationDatetime,
            "assignedTables": None,
            "suggestedDatetime": None,
            "suggestedTables": None,
        }

    # 3. Retourner une suggestion
    return {
        "isPossible": False,
        "requestedDatetime": request.reservationDatetime,
        "assignedTables": None,
        "suggestedDatetime": closest_datetime,
        "suggestedTables": closest_tables,
    }
