from src.bdd.dbmanager import DBManager
from src.models.order_draft import DraftOrder
from src.prompts.validatorPrompt import VALIDATOR_PROMPT
from src.config import gemini_settings
from src.utils.sse_manager import sse_manager, EventType


async def validate_order(order_text: str, customerName: str, customerPhone: str = "") -> dict:
    """
    Validates and saves a customer order using an LLM validator.
    
    This tool receives a natural language description of the order,
    sends it to a validation LLM that parses it into a structured format,
    validates against the menu, and saves to database if valid.
    
    Parameters:
    - order_text: str - Description textuelle de la commande (ex: "2 pizzas margherita, 1 tiramisu, une formule midi avec une calzone et un coca")
    - customerName: str - Nom du client (obligatoire)
    - customerPhone: str - Téléphone du client (optionnel)
    
    Returns:
    - dict avec "success", "message"
    """
    try:
        if not customerName or not customerName.strip():
            return {
                "success": False,
                "message": "Le nom du client est obligatoire pour valider la commande."
            }
        
        if not order_text or not order_text.strip():
            return {
                "success": False,
                "message": "La description de la commande est vide."
            }
        
        # 1. Récupérer le menu pour le contexte du validateur
        db_manager = DBManager()
        menu_items, menu_formules = await db_manager.get_menu()
        
        menu_str = "Items disponibles:\n"
        for item in menu_items:
            menu_str += f"- {item}\n"
        menu_str += "\nFormules disponibles:\n"
        for formule in menu_formules:
            menu_str += f"- {formule}\n"
        
        # 2. Construire le prompt pour le validateur
        prompt = VALIDATOR_PROMPT.format(
            menu=menu_str,
            order_text=order_text,
            customer_name=customerName,
            customer_phone=customerPhone or "Non fourni"
        )
        
        # 3. Appeler le LLM validateur
        try:
            response = await gemini_settings.CLIENT.aio.models.generate_content(
                model=gemini_settings.MODEL_NAME,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": DraftOrder,
                },
            )
        except Exception as err:
            raise ValueError(f"Gemini API call failed: {err}")
        
        try:
            draft_order: DraftOrder = DraftOrder.model_validate(response.parsed)
        except Exception as err:
            return {
                "success": False,
                "message": f"Erreur de parsing de la commande: {err}"
            }

        # Vérifier si le validateur a détecté une erreur
        if draft_order.error_message and draft_order.error_message.strip():
            return {
                "success": False,
                "message": draft_order.error_message
            }
        
        # Vérifier que la commande contient au moins un item ou une formule
        if not draft_order.items and not draft_order.formules:
            return {
                "success": False,
                "message": "La commande est vide. Veuillez ajouter au moins un item ou une formule."
            }
        
        # Sauvegarder en BDD
        try:
            order_id = await db_manager.save_full_order(draft_order, customerName, customerPhone)
        except Exception as db_err:
            return {
                "success": False,
                "message": f"Erreur lors de l'enregistrement en base de données: {str(db_err)}"
            }
        
        # Récupérer la commande complète depuis la BDD pour avoir tous les champs (created_at, updated_at, etc.)
        from sqlalchemy import select
        from src.bdd.schema import Order
        from sqlalchemy.orm import selectinload
        
        # Préparer les données SSE dans la session pour éviter le lazy loading
        sse_data = None
        async with db_manager.SessionLocal() as session:
            # Charger l'order avec ses relations (eager loading)
            query = select(Order).options(
                selectinload(Order.items),
                selectinload(Order.formules)
            ).where(Order.id == order_id)
            result = await session.execute(query)
            order = result.scalar_one_or_none()
            
            # Extraire les données DANS la session (avant que la session ne se ferme)
            if order:
                sse_data = {
                    "id": str(order.id),
                    "customer_name": order.customer_name,
                    "customer_phone": order.customer_phone,
                    "is_validated": order.is_validated,
                    "items_count": len(order.items),
                    "formules_count": len(order.formules),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                }
        
        # Publier l'événement SSE avec les données extraites
        if sse_data:
            try:
                await sse_manager.publish_order_event(EventType.ORDER_CREATED, sse_data)
            except Exception:
                pass  # Erreur SSE non bloquante
        
        return {
            "success": True,
            "message": "Commande validée et enregistrée avec succès!",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors de la validation de la commande: {str(e)}"
        }

