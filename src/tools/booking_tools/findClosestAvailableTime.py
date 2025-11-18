from datetime import datetime, timedelta
from .optimizeTableAssignment import optimize_table_assignment

def find_closest_available_time(
    tables,
    existing_reservations,
    requested_datetime: datetime,
    avg_duration_minutes: int,
    number_of_people: int,
    buffer_time_minutes: int,
    now: datetime | None = None,
    max_scan_minutes=180,
):
    if now is None:
        now = datetime.now()

    # 1) Tester immédiatement l'heure demandée
    result = optimize_table_assignment(
        tables,
        existing_reservations,
        requested_datetime,
        avg_duration_minutes,
        number_of_people,
        now
    )

    if result:
        return requested_datetime, result

    # 2) Chercher autour de l'heure
    step = timedelta(minutes=buffer_time_minutes)
    max_steps = max_scan_minutes // buffer_time_minutes

    for t in range(1, max_steps + 1):

        # Vers l'avant
        forward = requested_datetime + t * step
        res_fwd = optimize_table_assignment(
            tables,
            existing_reservations,
            forward,
            avg_duration_minutes,
            number_of_people,
            now
        )
        if res_fwd:
            return forward, res_fwd

        # Vers l'arrière
        backward = requested_datetime - t * step
        res_back = optimize_table_assignment(
            tables,
            existing_reservations,
            backward,
            avg_duration_minutes,
            number_of_people,
            now
        )
        if res_back:
            return backward, res_back

    return None, []
