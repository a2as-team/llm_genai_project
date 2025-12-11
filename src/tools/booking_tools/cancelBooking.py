"""
Booking cancellation tool for restaurant reservations.

This tool handles reservation cancellation with intelligent lookup:
- If exact match (phone + date) → cancel immediately
- If multiple matches → return all for user clarification
- If no match for date → search by phone only and suggest alternatives
- If nothing found → inform user no reservation exists
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID

from src.bdd.dbmanager import DBManager
from src.models.booking import CancelBookingResponse, ReservationSummary
from src.tools.booking_tools.validateBooking import parse_datetime_string

# Timezone du restaurant (Paris)
RESTAURANT_TZ = ZoneInfo("Europe/Paris")


def format_reservation_datetime(dt: datetime) -> str:
    """Format a datetime for display, converting to Paris time if needed."""
    if dt.tzinfo:
        dt = dt.astimezone(RESTAURANT_TZ)
    return dt.strftime('%d/%m/%Y à %Hh%M')


async def cancel_booking(
    phone_number: str,
    date: str,
    reservation_id: str = ""
) -> CancelBookingResponse:
    """
    Cancels a restaurant reservation.
    
    This tool handles reservation cancellation with the following workflow:
    
    1. If reservation_id is provided → delete directly
    2. Otherwise search by phone + date:
       - If unique match found → delete and confirm
       - If multiple matches → return all, ask user to clarify
       - If no match → search by phone only:
         - If found → return them, suggest user may have wrong date
         - If nothing → inform no reservation for this phone
    
    Parameters:
    - phone_number: Customer's phone number
    - date: Date of the reservation (various formats accepted)
    - reservation_id: Direct ID if user already specified which one (empty string if not provided)
    
    Returns:
    - CancelBookingResponse with success status, message, and found reservations if any
    """
    db_manager = DBManager()
    
    try:
        # Case 1: Direct deletion by ID
        if reservation_id and reservation_id.strip():
            try:
                res_uuid = UUID(reservation_id)
                await db_manager.delete_reservation(res_uuid)
                return CancelBookingResponse(
                    success=True,
                    message="Votre réservation a été annulée avec succès.",
                    reservations_found=None
                )
            except ValueError:
                return CancelBookingResponse(
                    success=False,
                    message="Identifiant de réservation invalide.",
                    reservations_found=None
                )
        
        # Parse the date string
        try:
            target_date = parse_datetime_string(date)
        except ValueError as e:
            return CancelBookingResponse(
                success=False,
                message=str(e),
                reservations_found=None
            )
        
        # Case 2: Search by phone + date
        reservations = await db_manager.find_reservations_by_phone_and_date(
            phone=phone_number,
            target_date=target_date
        )
        
        if len(reservations) == 1:
            # Unique match - delete it
            res = reservations[0]
            await db_manager.delete_reservation(res["id"])
            
            res_dt = res["reservation_datetime"]
            formatted_dt = format_reservation_datetime(res_dt)
            
            return CancelBookingResponse(
                success=True,
                message=f"Votre réservation du {formatted_dt} pour {res['number_of_guests']} personnes "
                        f"au nom de {res['customer_name']} a été annulée avec succès.",
                reservations_found=None
            )
        
        if len(reservations) > 1:
            # Multiple matches - ask user to clarify
            summaries = [
                ReservationSummary(
                    id=res["id"],
                    reservation_datetime=format_reservation_datetime(res["reservation_datetime"]),
                    number_of_guests=res["number_of_guests"],
                    customer_name=res["customer_name"]
                )
                for res in reservations
            ]
            
            return CancelBookingResponse(
                success=False,
                message=f"Plusieurs réservations trouvées pour le {target_date.strftime('%d/%m/%Y')} "
                        f"avec ce numéro de téléphone. Veuillez préciser laquelle vous souhaitez annuler:",
                reservations_found=summaries
            )
        
        # Case 3: No match for this date - search by phone only
        all_reservations = await db_manager.find_reservations_by_phone(phone=phone_number)
        
        if all_reservations:
            # Found reservations for other dates
            summaries = [
                ReservationSummary(
                    id=res["id"],
                    reservation_datetime=format_reservation_datetime(res["reservation_datetime"]),
                    number_of_guests=res["number_of_guests"],
                    customer_name=res["customer_name"]
                )
                for res in all_reservations
            ]
            
            return CancelBookingResponse(
                success=False,
                message=f"Aucune réservation trouvée pour le {target_date.strftime('%d/%m/%Y')}. "
                        f"Cependant, j'ai trouvé ces réservations associées à votre numéro de téléphone. "
                        f"Est-ce l'une de celles-ci que vous souhaitez annuler?",
                reservations_found=summaries
            )
        
        # Case 4: No reservations at all for this phone
        return CancelBookingResponse(
            success=False,
            message=f"Aucune réservation n'a été trouvée pour le numéro {phone_number}. "
                    "Veuillez vérifier le numéro de téléphone utilisé lors de la réservation.",
            reservations_found=None
        )
        
    except Exception as e:
        print(f"[cancel_booking] Exception: {e}")
        return CancelBookingResponse(
            success=False,
            message=f"Erreur lors de l'annulation de la réservation: {str(e)}",
            reservations_found=None
        )