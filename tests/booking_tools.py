from src.tools import validate_booking
from src.models import *
from datetime import datetime


async def test_validate_booking():

    booking_request = BookingRequest(
        reservation_datetime="2024-12-24T19:30:00",
        number_of_guests=10,
        location="outdoor",
        customer_name="John Trois",
        customer_phone="123-456-7890",
        extra_infos=None
    )

    response: BookingResponse = await validate_booking(booking_request)

    print("Booking Validation Response:", response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_validate_booking())