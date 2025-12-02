"""Test script to verify Orders and Reservations routes."""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/data"

async def test_routes():
    """Test all the new routes."""
    
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("TESTING ORDERS & RESERVATIONS ROUTES")
        print("=" * 80)
        
        # ========================
        # ORDERS TESTS
        # ========================
        print("\n📦 TESTING ORDERS ENDPOINTS:\n")
        
        # Test 1: Get all orders
        print("1️⃣  GET /api/data/orders")
        try:
            response = await client.get(f"{BASE_URL}/orders?skip=0&limit=10")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {len(data)} orders")
                if data:
                    print(f"   Sample: {json.dumps(data[0], indent=2)}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 2: Get validated orders
        print("\n2️⃣  GET /api/data/orders/validated")
        try:
            response = await client.get(f"{BASE_URL}/orders/validated")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {len(data)} validated orders")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 3: Get pending orders
        print("\n3️⃣  GET /api/data/orders/pending")
        try:
            response = await client.get(f"{BASE_URL}/orders/pending")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {len(data)} pending orders")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 4: Get order by ID (if we have one)
        print("\n4️⃣  GET /api/data/orders/{{order_id}}")
        try:
            response = await client.get(f"{BASE_URL}/orders")
            if response.status_code == 200:
                orders = response.json()
                if orders:
                    order_id = orders[0]["id"]
                    response = await client.get(f"{BASE_URL}/orders/{order_id}")
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        print(f"   ✅ Order details retrieved")
                        order = response.json()
                        print(f"      - Customer: {order.get('customer_name')}")
                        print(f"      - Formules: {len(order.get('formules', []))}")
                        print(f"      - Items: {len(order.get('items', []))}")
                    else:
                        print(f"   ❌ Error: {response.text}")
                else:
                    print("   ⚠️  No orders found to test")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # ========================
        # RESERVATIONS TESTS
        # ========================
        print("\n\n📅 TESTING RESERVATIONS ENDPOINTS:\n")
        
        # Test 5: Get all reservations
        print("5️⃣  GET /api/data/reservations")
        try:
            response = await client.get(f"{BASE_URL}/reservations?skip=0&limit=10")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {len(data)} reservations")
                if data:
                    print(f"   Sample: {json.dumps(data[0], indent=2)}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 6: Get upcoming reservations
        print("\n6️⃣  GET /api/data/reservations/upcoming")
        try:
            response = await client.get(f"{BASE_URL}/reservations/upcoming")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {len(data)} upcoming reservations")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 7: Get reservation by ID (if we have one)
        print("\n7️⃣  GET /api/data/reservations/{{reservation_id}}")
        try:
            response = await client.get(f"{BASE_URL}/reservations")
            if response.status_code == 200:
                reservations = response.json()
                if reservations:
                    reservation_id = reservations[0]["id"]
                    response = await client.get(f"{BASE_URL}/reservations/{reservation_id}")
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        print(f"   ✅ Reservation details retrieved")
                        reservation = response.json()
                        print(f"      - Customer: {reservation.get('customer_name')}")
                        print(f"      - Date: {reservation.get('reservation_datetime')}")
                        print(f"      - Guests: {reservation.get('number_of_guests')}")
                        print(f"      - Tables: {len(reservation.get('tables', []))}")
                    else:
                        print(f"   ❌ Error: {response.text}")
                else:
                    print("   ⚠️  No reservations found to test")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        # Test 8: Get reservations by date
        print("\n8️⃣  GET /api/data/reservations/date/{{date}}")
        try:
            from datetime import datetime, timedelta
            today = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            response = await client.get(f"{BASE_URL}/reservations/date/{today}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {len(data)} reservations for {today}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        print("\n" + "=" * 80)
        print("✅ TEST SUITE COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    print("\n🚀 Make sure your FastAPI server is running on http://localhost:8000")
    print("   Run: python -m src.app.main (or your startup script)\n")
    asyncio.run(test_routes())
