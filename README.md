# llm_genai_project
Voice-Enabled Generative AI Restaurant Assistant

This project aims to develop a voice-interactive Generative AI assistant that acts as a virtual 
receptionist for a restaurant. The system should be capable of engaging in natural two-way 
spoken conversations with customers, understanding their voice queries, interpreting intent, and 
responding with generated speech in real time. 
The assistant will handle multiple receptionist-style tasks such as: 
• Table reservations: taking booking details (name, date, time, number of guests) and 
confirming availability. 
• Order handling: taking take-away or delivery orders, confirming menu items, and 
repeating orders for validation. 
• Menu information: answering questions about dishes, ingredients, allergens, or 
promotions. 
• General inquiries: providing restaurant location, opening hours, or special offers. 
The result will be a fully voice-driven AI receptionist that simulates a real conversational 
restaurant assistant, capable of operating offline (using local models via Ollama) or online (using 
APIs such as Google AI SDK).


Zephyr : Lumineux	Puck : Upbeat	Charon : Contenu informatif
Kore : ferme	Fenrir : excitabilité	Leda : Jeune
Orus : cabinet d'avocats	Aoede : Breezy	Callirrhoe : tranquille
Autonoe : Lumineux	Enceladus : Souffle	Iapetus : Effacer
Umbriel : décontracté	Algieba : Smooth	Despina : Lisse
Erinome : dégagé	Algenib : Graveleux	Rasalgethi : informatif
Laomedeia : Upbeat	Achernar : Soft	Alnilam : Ferme
Schedar : Even	Gacrux : Contenu réservé aux adultes	Pulcherrima : franche
Achird : amical	Zubenelgenubi : Décontracté	Vindemiatrix : Doux
Sadachbia : Lively	Sadaltager : connaissances	Sulafat : chaude


### TO DO

- Faire une fonction de validation qui va utiliser un llm ou un truc de sémantique pour s'assurer que les noms d'items/Formules choisis par le modèle existe bien en db, le modèle que manipule le llm sera beaucoup plus simple
- Faire en sorte que update item et add item et tout ty quointi ça prenne des listes
- faire en sorte de check si y'a de la places et pour combien de personnes avant de prendre les détails d'une résa donc injecter au modèle quand l'app se lance dans le sys prompt disponible pour combien de personnes maximums avec une petite query db !
- Mettre les guardails dans le sys prompt, l'empecher de book dans le passé, d'essayer de réserver pour 100 personnes etc il faut que il n'y ait que des trucs plausibles qui arrivent dans le tool de validation de booking.

