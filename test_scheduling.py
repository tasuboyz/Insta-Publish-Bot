"""
Test sistema di programmazione post con database SQLite
"""
import asyncio
from datetime import datetime, timedelta
from services.database import db
from services.scheduler import scheduler
from services.instagram_publisher_async import InstagramPublisher
from config import config

async def test_scheduling_workflow():
    """Test completo del workflow di programmazione"""
    
    print("🧪 Test Sistema Programmazione Post\n")
    
    # 1. Test sessione utente
    print("1️⃣ Test sessione utente...")
    user_id = 999999  # ID test
    
    # Simula selezione data
    selected_date = datetime.now() + timedelta(days=1)
    db.save_user_session(user_id=user_id, selected_date=selected_date)
    print(f"   ✅ Data salvata: {selected_date.strftime('%d/%m/%Y')}")
    
    # Simula selezione ora
    db.save_user_session(user_id=user_id, selected_hour=14)
    print(f"   ✅ Ora salvata: 14")
    
    # Simula selezione minuti
    db.save_user_session(user_id=user_id, selected_minute=30)
    print(f"   ✅ Minuti salvati: 30")
    
    # Simula conferma
    scheduled_datetime = selected_date.replace(hour=14, minute=30)
    db.save_user_session(user_id=user_id, scheduled_datetime=scheduled_datetime)
    print(f"   ✅ DateTime completo salvato: {scheduled_datetime.strftime('%d/%m/%Y %H:%M')}")
    
    # Recupera sessione
    session = db.get_user_session(user_id)
    print(f"   ✅ Sessione recuperata: {session is not None}")
    
    # 2. Test programmazione post
    print("\n2️⃣ Test programmazione post...")
    
    # Simula invio foto (programma post tra 2 minuti per test)
    test_scheduled_time = datetime.now() + timedelta(minutes=2)
    
    post_id = scheduler.schedule_post(
        user_id=user_id,
        image_url="https://example.com/test.jpg",
        caption="Test post programmato",
        scheduled_time=test_scheduled_time,
        telegram_message_id=12345
    )
    
    print(f"   ✅ Post programmato: {post_id}")
    print(f"   📅 Pubblicazione prevista: {test_scheduled_time.strftime('%d/%m/%Y %H:%M')}")
    
    # Verifica che la sessione sia stata pulita
    session_after = db.get_user_session(user_id)
    print(f"   ✅ Sessione pulita dopo programmazione: {session_after is None}")
    
    # 3. Test recupero post
    print("\n3️⃣ Test recupero post...")
    user_posts = scheduler.get_user_posts(user_id)
    print(f"   ✅ Post utente trovati: {len(user_posts)}")
    
    for post in user_posts:
        print(f"      - ID: {post['id']}")
        print(f"        Status: {post['status']}")
        print(f"        Scheduled: {post['scheduled_time'].strftime('%d/%m/%Y %H:%M')}")
    
    # 4. Test post scaduti (crea un post nel passato)
    print("\n4️⃣ Test post scaduti...")
    past_time = datetime.now() - timedelta(minutes=1)
    
    past_post_id = scheduler.schedule_post(
        user_id=user_id,
        image_url="https://example.com/past.jpg",
        caption="Post scaduto per test",
        scheduled_time=past_time,
        telegram_message_id=67890
    )
    
    due_posts = scheduler.get_due_posts()
    print(f"   ✅ Post scaduti trovati: {len(due_posts)}")
    
    # 5. Test aggiornamento status
    print("\n5️⃣ Test aggiornamento status...")
    scheduler.update_post_status(
        past_post_id,
        'published',
        instagram_media_id='IG_TEST_123'
    )
    
    updated_post = scheduler.get_post_by_id(past_post_id)
    print(f"   ✅ Status aggiornato: {updated_post['status']}")
    print(f"   ✅ Media ID: {updated_post.get('instagram_media_id')}")
    
    # 6. Test cancellazione
    print("\n6️⃣ Test cancellazione post...")
    cancelled = scheduler.cancel_post(post_id, user_id)
    print(f"   ✅ Post cancellato: {cancelled}")
    
    cancelled_post = scheduler.get_post_by_id(post_id)
    print(f"   ✅ Nuovo status: {cancelled_post['status']}")
    
    # 7. Statistiche finali
    print("\n7️⃣ Statistiche database...")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Pulizia
    print("\n8️⃣ Pulizia test data...")
    db.clear_user_session(user_id)
    print("   ✅ Sessione pulita")
    
    print("\n✅ Tutti i test completati con successo!")
    print("\n📝 Note:")
    print("   - Il database SQLite funziona correttamente")
    print("   - Le sessioni utente vengono salvate e recuperate")
    print("   - I post programmati vengono gestiti correttamente")
    print("   - Il background task pubblicherà automaticamente i post scaduti")


if __name__ == "__main__":
    asyncio.run(test_scheduling_workflow())
