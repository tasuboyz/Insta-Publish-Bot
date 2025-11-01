"""
Generate initial Instagram access token using Facebook App credentials.

This script will:
1. Prompt for a short-lived user access token (get from Graph API Explorer)
2. Exchange it for a long-lived token
3. Try to find the Instagram Business Account
4. Save the token to .env

Usage:
    python generate_token.py
"""
import asyncio
import sys
from pathlib import Path
from services.token_manager import exchange_long_lived, persist_token_to_env, get_page_access_token, BASE_URL
from config import config
import httpx


async def find_instagram_account(user_token: str):
    """Try to find Instagram Business Account from user's pages."""
    print("\n🔍 Cercando Instagram Business Account...")
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Get user's pages
            r = await client.get(
                f"{BASE_URL}/me/accounts",
                params={"access_token": user_token}
            )
            r.raise_for_status()
            pages = r.json().get('data', [])
            
            if not pages:
                print("❌ Nessuna pagina Facebook trovata per questo token")
                return None
            
            print(f"✅ Trovate {len(pages)} pagine")
            
            # Check each page for Instagram Business Account
            for page in pages:
                page_id = page.get('id')
                page_name = page.get('name', 'Unknown')
                
                # Get Instagram account linked to this page
                r2 = await client.get(
                    f"{BASE_URL}/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": user_token
                    }
                )
                r2.raise_for_status()
                ig_data = r2.json()
                
                ig_account = ig_data.get('instagram_business_account')
                if ig_account:
                    ig_id = ig_account.get('id')
                    print(f"\n✅ Trovato Instagram Business Account!")
                    print(f"   Page: {page_name} (ID: {page_id})")
                    print(f"   Instagram Account ID: {ig_id}")
                    
                    # Get page access token
                    page_token = page.get('access_token')
                    if page_token:
                        print(f"   Page Access Token: {page_token[:20]}...")
                        return {
                            'instagram_account_id': ig_id,
                            'page_id': page_id,
                            'page_name': page_name,
                            'page_token': page_token
                        }
            
            print("❌ Nessun Instagram Business Account trovato")
            return None
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        return None


async def main():
    """Main flow to generate token."""
    print("=" * 70)
    print("  📸 Instagram Token Generator")
    print("=" * 70)
    
    # Check app credentials
    if not config.instagram.app_id or not config.instagram.app_secret:
        print("\n❌ FACEBOOK_APP_ID e FACEBOOK_APP_SECRET devono essere configurati in .env")
        print("   Aggiungi questi valori e riprova.")
        sys.exit(1)
    
    print(f"\n✅ App ID: {config.instagram.app_id}")
    print(f"✅ App Secret: {'*' * 20}")
    
    # Instructions for getting short-lived token
    print("\n" + "=" * 70)
    print("STEP 1: Ottieni un User Access Token")
    print("=" * 70)
    print("\n1. Vai su Graph API Explorer:")
    print("   https://developers.facebook.com/tools/explorer/")
    print("\n2. Seleziona la tua app dal menu")
    print("\n3. Richiedi questi permessi:")
    print("   - instagram_basic")
    print("   - instagram_content_publish")
    print("   - pages_read_engagement")
    print("   - pages_show_list")
    print("\n4. Clicca 'Generate Access Token'")
    print("\n5. Copia il token generato")
    
    print("\n" + "-" * 70)
    short_token = input("\nIncolla il token qui: ").strip()
    
    if not short_token:
        print("❌ Nessun token fornito")
        sys.exit(1)
    
    # Exchange for long-lived token
    print("\n" + "=" * 70)
    print("STEP 2: Scambio token per long-lived")
    print("=" * 70)
    
    result = await exchange_long_lived(short_token)
    if not result:
        print("❌ Errore nello scambio del token")
        print("   Verifica che:")
        print("   - Il token sia valido")
        print("   - App ID e Secret siano corretti")
        print("   - Il token abbia i permessi necessari")
        sys.exit(1)
    
    long_token = result.get('access_token')
    expires_in = result.get('expires_in', 0)
    
    print(f"✅ Token long-lived ottenuto!")
    print(f"   Scade tra: {expires_in // 86400} giorni")
    print(f"   Token: {long_token[:30]}...")
    
    # Find Instagram account
    ig_info = await find_instagram_account(long_token)
    
    # Save token to .env
    print("\n" + "=" * 70)
    print("STEP 3: Salvataggio configurazione")
    print("=" * 70)
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ File .env non trovato")
        sys.exit(1)
    
    # Read current .env
    content = env_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    # Update lines
    new_lines = []
    token_set = False
    account_set = False
    
    for line in lines:
        if line.strip().startswith('INSTAGRAM_ACCESS_TOKEN='):
            new_lines.append(f'INSTAGRAM_ACCESS_TOKEN={long_token}')
            token_set = True
        elif line.strip().startswith('INSTAGRAM_ACCOUNT_ID=') and ig_info:
            new_lines.append(f'INSTAGRAM_ACCOUNT_ID={ig_info["instagram_account_id"]}')
            account_set = True
        else:
            new_lines.append(line)
    
    # Add if not present
    if not token_set:
        new_lines.append(f'\nINSTAGRAM_ACCESS_TOKEN={long_token}')
    
    if not account_set and ig_info:
        new_lines.append(f'INSTAGRAM_ACCOUNT_ID={ig_info["instagram_account_id"]}')
    
    # Write back
    env_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    
    print("\n✅ Token salvato in .env")
    if ig_info:
        print(f"✅ Instagram Account ID aggiornato: {ig_info['instagram_account_id']}")
        print(f"   Collegato alla pagina: {ig_info['page_name']}")
    
    print("\n" + "=" * 70)
    print("✅ COMPLETATO!")
    print("=" * 70)
    print("\nIl bot è ora configurato e pronto per l'uso.")
    print("Avvia il bot con: python run.py")
    print("\nIl token verrà automaticamente rinnovato prima della scadenza.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operazione annullata")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
