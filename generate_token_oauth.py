"""
Generate Instagram access token using OAuth flow (no Graph API Explorer needed).

This script will:
1. Generate OAuth authorization URL
2. You visit URL and authorize the app
3. Facebook redirects with a code
4. Script exchanges code for access token
5. Exchanges for long-lived token
6. Saves to .env

Usage:
    python generate_token_oauth.py
"""
import asyncio
import sys
import urllib.parse
from pathlib import Path
import httpx
from config import config


# OAuth redirect URI - must match what's configured in Facebook App
REDIRECT_URI = "https://localhost/"  # or your configured redirect URI


async def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    url = "https://graph.facebook.com/v23.0/oauth/access_token"
    params = {
        "client_id": config.instagram.app_id,
        "client_secret": config.instagram.app_secret,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"❌ Errore scambio code: {e}")
        try:
            print(f"   Response: {r.text}")
        except:
            pass
        return None


async def exchange_long_lived(token: str) -> dict:
    """Exchange short-lived token for long-lived."""
    url = "https://graph.facebook.com/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": config.instagram.app_id,
        "client_secret": config.instagram.app_secret,
        "fb_exchange_token": token
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"❌ Errore exchange long-lived: {e}")
        try:
            print(f"   Response: {r.text}")
        except:
            pass
        return None


async def find_instagram_account(user_token: str):
    """Find Instagram Business Account from user's pages."""
    print("\n🔍 Cercando Instagram Business Account...")
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                f"https://graph.facebook.com/v23.0/me/accounts",
                params={"access_token": user_token}
            )
            r.raise_for_status()
            pages = r.json().get('data', [])
            
            if not pages:
                print("❌ Nessuna pagina trovata")
                return None
            
            print(f"✅ Trovate {len(pages)} pagine")
            
            for page in pages:
                page_id = page.get('id')
                page_name = page.get('name', 'Unknown')
                
                r2 = await client.get(
                    f"https://graph.facebook.com/v23.0/{page_id}",
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
                    print(f"   Page: {page_name}")
                    print(f"   Instagram Account ID: {ig_id}")
                    return {
                        'instagram_account_id': ig_id,
                        'page_name': page_name
                    }
            
            print("❌ Nessun Instagram Business Account trovato")
            return None
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        return None


def save_to_env(token: str, ig_id: str = None):
    """Save token (and optionally ig_id) to .env."""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ File .env non trovato")
        return False
    
    content = env_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    new_lines = []
    token_set = False
    account_set = False
    
    for line in lines:
        if line.strip().startswith('INSTAGRAM_ACCESS_TOKEN='):
            new_lines.append(f'INSTAGRAM_ACCESS_TOKEN={token}')
            token_set = True
        elif line.strip().startswith('INSTAGRAM_ACCOUNT_ID=') and ig_id:
            new_lines.append(f'INSTAGRAM_ACCOUNT_ID={ig_id}')
            account_set = True
        else:
            new_lines.append(line)
    
    if not token_set:
        new_lines.append(f'\nINSTAGRAM_ACCESS_TOKEN={token}')
    
    if not account_set and ig_id:
        new_lines.append(f'INSTAGRAM_ACCOUNT_ID={ig_id}')
    
    env_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    return True


async def main():
    """Main OAuth flow."""
    print("=" * 70)
    print("  📸 Instagram Token Generator - OAuth Flow")
    print("=" * 70)
    
    # Check credentials
    if not config.instagram.app_id or not config.instagram.app_secret:
        print("\n❌ FACEBOOK_APP_ID e FACEBOOK_APP_SECRET devono essere in .env")
        sys.exit(1)
    
    print(f"\n✅ App ID: {config.instagram.app_id}")
    
    # Step 1: Generate authorization URL
    permissions = [
        'instagram_basic',
        'instagram_content_publish',
        'pages_read_engagement',
        'pages_show_list'
    ]
    
    auth_params = {
        'client_id': config.instagram.app_id,
        'redirect_uri': REDIRECT_URI,
        'scope': ','.join(permissions),
        'response_type': 'code'
    }
    
    auth_url = f"https://www.facebook.com/v23.0/dialog/oauth?{urllib.parse.urlencode(auth_params)}"
    
    print("\n" + "=" * 70)
    print("STEP 1: Autorizza l'applicazione")
    print("=" * 70)
    print("\n1. Apri questo URL nel browser:\n")
    print(auth_url)
    print("\n2. Fai login con Facebook e autorizza l'app")
    print("\n3. Facebook ti reindirizzerà a un URL tipo:")
    print(f"   {REDIRECT_URI}?code=XXXXXXXXX")
    print("\n4. Copia TUTTO l'URL di reindirizzamento")
    
    print("\n" + "-" * 70)
    redirect_response = input("\nIncolla l'URL completo qui: ").strip()
    
    if not redirect_response:
        print("❌ Nessun URL fornito")
        sys.exit(1)
    
    # Extract code from URL
    try:
        parsed = urllib.parse.urlparse(redirect_response)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get('code', [None])[0]
        
        if not code:
            print("❌ Nessun 'code' trovato nell'URL")
            print("   L'URL deve contenere: ?code=...")
            sys.exit(1)
        
        print(f"\n✅ Code estratto: {code[:20]}...")
        
    except Exception as e:
        print(f"❌ Errore parsing URL: {e}")
        sys.exit(1)
    
    # Step 2: Exchange code for token
    print("\n" + "=" * 70)
    print("STEP 2: Scambio code per access token")
    print("=" * 70)
    
    token_data = await exchange_code_for_token(code)
    if not token_data:
        print("❌ Errore nello scambio del code")
        print("\n⚠️  Possibili cause:")
        print("   - Il code è già stato usato (scade dopo 1 uso)")
        print("   - Il redirect_uri non corrisponde a quello configurato nell'app")
        print("   - App ID o Secret non corretti")
        print(f"\n   Redirect URI configurato in questo script: {REDIRECT_URI}")
        print("   Verifica che corrisponda a quello in Facebook App Settings")
        sys.exit(1)
    
    short_token = token_data.get('access_token')
    print(f"✅ Token short-lived ottenuto: {short_token[:30]}...")
    
    # Step 3: Exchange for long-lived
    print("\n" + "=" * 70)
    print("STEP 3: Scambio per long-lived token")
    print("=" * 70)
    
    long_data = await exchange_long_lived(short_token)
    if not long_data:
        print("❌ Errore exchange long-lived")
        sys.exit(1)
    
    long_token = long_data.get('access_token')
    expires_in = long_data.get('expires_in', 0)
    
    print(f"✅ Token long-lived ottenuto!")
    print(f"   Scade tra: {expires_in // 86400} giorni")
    print(f"   Token: {long_token[:30]}...")
    
    # Step 4: Find Instagram account
    ig_info = await find_instagram_account(long_token)
    
    # Step 5: Save
    print("\n" + "=" * 70)
    print("STEP 4: Salvataggio in .env")
    print("=" * 70)
    
    ig_id = ig_info['instagram_account_id'] if ig_info else None
    ok = save_to_env(long_token, ig_id)
    
    if ok:
        print("\n✅ Token salvato in .env")
        if ig_id:
            print(f"✅ Instagram Account ID aggiornato: {ig_id}")
    else:
        print("\n⚠️  Errore salvataggio, ma il token è:")
        print(f"   {long_token}")
        print("\n   Aggiungilo manualmente a .env come:")
        print(f"   INSTAGRAM_ACCESS_TOKEN={long_token}")
    
    print("\n" + "=" * 70)
    print("✅ COMPLETATO!")
    print("=" * 70)
    print("\nAvvia il bot con: python run.py")


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
