from ortools.sat.python import cp_model
from datetime import datetime, timedelta


def is_locked(reservation, now: datetime, avg_duration_minutes: int):
    start = reservation.reservationDatetime
    end = start + timedelta(minutes=avg_duration_minutes)
    return start - timedelta(minutes=15) <= now <= end


def tables_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def optimize_table_assignment(
    tables,
    existing_reservations,
    reservation_datetime: datetime,
    avg_duration_minutes: int,
    number_of_people: int,
    now: datetime | None = None
):
    if now is None:
        now = datetime.now()

    model = cp_model.CpModel()

    new_start = reservation_datetime
    new_end = reservation_datetime + timedelta(minutes=avg_duration_minutes)

    # Variables : x[i] = 1 si on choisit la table i
    x = {
        i: model.NewBoolVar(f"use_table_{i}")
        for i in range(len(tables))
    }

    # Contrainte de disponibilité
    for i, table in enumerate(tables):
        for res in existing_reservations:
            start = res.reservationDatetime
            end = start + timedelta(minutes=avg_duration_minutes)

            if tables_overlap(start, end, new_start, new_end) and table.id in res.tableIds:
                    model.Add(x[i] == 0)

    # Capacité totale ≥ invités
    model.Add(
        sum(t.capacity * x[i] for i, t in enumerate(tables)) >= number_of_people
    )

    # Contrainte de combinabilité
    for i, table in enumerate(tables):
        if table.combinable_with:
            for j, other in enumerate(tables):
                if other.id not in table.combinable_with and other.id != table.id:
                    model.Add(x[j] == 0).OnlyEnforceIf(x[i])

    # Objectif : minimiser nombre de tables + gaspillage
    total_capacity = sum(t.capacity * x[i] for i, t in enumerate(tables))
    waste = total_capacity - number_of_people
    model.Minimize(1000 * sum(x.values()) + waste)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    return [
        tables[i]
        for i in range(len(tables))
        if solver.Value(x[i]) == 1
    ]
