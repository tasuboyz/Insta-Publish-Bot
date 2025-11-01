"""
Handlers per calendario e programmazione post
"""
import calendar
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import Message
from services.scheduler import scheduler
from services.database import db

logger = logging.getLogger(__name__)

# Router per calendario
calendar_router = Router()


def create_calendar_keyboard(year: int, month: int, selected_date: datetime = None) -> InlineKeyboardMarkup:
    """
    Crea tastiera inline per calendario

    Args:
        year: Anno
        month: Mese (1-12)
        selected_date: Data selezionata (opzionale)

    Returns:
        InlineKeyboardMarkup con calendario
    """
    # Giorni della settimana
    weekdays = ['L', 'M', 'M', 'G', 'V', 'S', 'D']

    # Ottieni calendario per il mese
    cal = calendar.monthcalendar(year, month)

    # Bottoni calendario
    keyboard = []

    # Header con mese/anno e navigazione
    header_row = [
        InlineKeyboardButton(
            text="◀️",
            callback_data=f"calendar_nav_{year}_{month-1}"
        ),
        InlineKeyboardButton(
            text=f"{calendar.month_name[month]} {year}",
            callback_data="calendar_ignore"
        ),
        InlineKeyboardButton(
            text="▶️",
            callback_data=f"calendar_nav_{year}_{month+1}"
        )
    ]
    keyboard.append(header_row)

    # Giorni della settimana
    weekday_row = [InlineKeyboardButton(text=day, callback_data="calendar_ignore") for day in weekdays]
    keyboard.append(weekday_row)

    # Giorni del mese
    for week in cal:
        week_row = []
        for day in week:
            if day == 0:
                # Giorno di un altro mese
                week_row.append(InlineKeyboardButton(text=" ", callback_data="calendar_ignore"))
            else:
                # Giorno del mese corrente
                date = datetime(year, month, day)
                today = datetime.now().date()

                # Determina se il giorno è selezionato o oggi
                if selected_date and date.date() == selected_date.date():
                    text = f"[{day}]"
                elif date.date() == today:
                    text = f"({day})"
                elif date.date() < today:
                    text = f"{day}❌"  # Giorni passati non selezionabili
                else:
                    text = str(day)

                # Callback data
                if date.date() >= today:
                    callback_data = f"calendar_day_{year}_{month}_{day}"
                else:
                    callback_data = "calendar_ignore"

                week_row.append(InlineKeyboardButton(text=text, callback_data=callback_data))

        keyboard.append(week_row)

    # Riga di controllo
    control_row = [
        InlineKeyboardButton(text="Annulla", callback_data="calendar_cancel"),
        InlineKeyboardButton(text="Oggi", callback_data=f"calendar_today_{year}_{month}")
    ]
    keyboard.append(control_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_time_keyboard(selected_hour: int = None, selected_minute: int = None) -> InlineKeyboardMarkup:
    """
    Crea tastiera inline per selezione ora

    Args:
        selected_hour: Ora selezionata (0-23)
        selected_minute: Minuto selezionato (0, 15, 30, 45)

    Returns:
        InlineKeyboardMarkup per selezione ora
    """
    keyboard = []

    # Ore (in gruppi di 6)
    hours = list(range(24))
    for i in range(0, 24, 6):
        hour_row = []
        for hour in hours[i:i+6]:
            text = f"{hour:02d}"
            if selected_hour == hour:
                text = f"[{text}]"
            hour_row.append(InlineKeyboardButton(
                text=text,
                callback_data=f"time_hour_{hour}"
            ))
        keyboard.append(hour_row)

    # Minuti
    minute_options = [0, 15, 30, 45]
    minute_row = []
    for minute in minute_options:
        text = f"{minute:02d}"
        if selected_minute == minute:
            text = f"[{text}]"
        minute_row.append(InlineKeyboardButton(
            text=text,
            callback_data=f"time_minute_{minute}"
        ))
    keyboard.append(minute_row)

    # Controlli
    control_row = [
        InlineKeyboardButton(text="🔙 Indietro", callback_data="time_back"),
        InlineKeyboardButton(text="Conferma", callback_data="time_confirm"),
        InlineKeyboardButton(text="Annulla", callback_data="time_cancel")
    ]
    keyboard.append(control_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@calendar_router.message(Command("schedule"))
async def cmd_schedule(message: Message):
    """Handler per comando /schedule - avvia programmazione post"""
    # Verifica che l'utente abbia inviato una foto recente
    # Per ora mostriamo il calendario per selezionare la data
    now = datetime.now()

    text = (
        "📅 <b>Programma un Post</b>\n\n"
        "Seleziona la data per la pubblicazione:\n\n"
        "<i>Nota: puoi programmare solo per date future</i>"
    )

    keyboard = create_calendar_keyboard(now.year, now.month)

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@calendar_router.callback_query(F.data.startswith("calendar_"))
async def handle_calendar_callback(callback: CallbackQuery):
    """Handler per callback calendario"""
    data = callback.data
    user_id = callback.from_user.id

    if data == "calendar_ignore":
        await callback.answer()
        return

    if data == "calendar_cancel":
        await callback.message.edit_text("❌ Programmazione annullata")
        await callback.answer()
        return

    if data.startswith("calendar_nav_"):
        # Navigazione mesi
        _, _, year, month = data.split("_")
        year, month = int(year), int(month)

        # Gestisci cambio anno
        if month == 0:
            month = 12
            year -= 1
        elif month == 13:
            month = 1
            year += 1

        keyboard = create_calendar_keyboard(year, month)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()

    elif data.startswith("calendar_today_"):
        # Vai a oggi
        _, _, year, month = data.split("_")
        year, month = int(year), int(month)

        today = datetime.now()
        keyboard = create_calendar_keyboard(today.year, today.month, today)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()

    elif data.startswith("calendar_day_"):
        # Giorno selezionato - passa alla selezione ora
        _, _, year, month, day = data.split("_")
        selected_date = datetime(int(year), int(month), int(day))

        # Salva la data selezionata nel database
        db.save_user_session(
            user_id=user_id,
            selected_date=selected_date
        )

        text = (
            f"📅 Data selezionata: <b>{selected_date.strftime('%d/%m/%Y')}</b>\n\n"
            "Ora seleziona l'orario:"
        )

        keyboard = create_time_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()


@calendar_router.callback_query(F.data.startswith("time_"))
async def handle_time_callback(callback: CallbackQuery):
    """Handler per callback selezione ora"""
    data = callback.data
    user_id = callback.from_user.id

    # Recupera la sessione utente dal database
    session = db.get_user_session(user_id)
    
    if not session or not session.get('selected_date'):
        await callback.message.edit_text("❌ Errore: sessione scaduta. Riprova con /schedule")
        await callback.answer()
        return

    selected_date = session['selected_date']

    if data == "time_back":
        # Torna al calendario
        text = (
            "📅 <b>Programma un Post</b>\n\n"
            "Seleziona la data per la pubblicazione:\n\n"
            "<i>Nota: puoi programmare solo per date future</i>"
        )
        keyboard = create_calendar_keyboard(selected_date.year, selected_date.month, selected_date)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return

    if data == "time_cancel":
        # Cancella sessione
        db.clear_user_session(user_id)
        await callback.message.edit_text("❌ Programmazione annullata")
        await callback.answer()
        return

    if data == "time_confirm":
        # Verifica che ora e minuti siano stati selezionati
        selected_hour = session.get('selected_hour')
        selected_minute = session.get('selected_minute')
        
        if selected_hour is None or selected_minute is None:
            await callback.answer("⚠️ Seleziona prima ora e minuti!", show_alert=True)
            return
        
        # Crea datetime completo
        scheduled_datetime = selected_date.replace(hour=selected_hour, minute=selected_minute)
        
        # Salva nel database
        db.save_user_session(user_id=user_id, scheduled_datetime=scheduled_datetime)
        
        text = (
            f"🕐 <b>Orario programmato:</b> {scheduled_datetime.strftime('%d/%m/%Y %H:%M')}\n\n"
            "✅ <b>Perfetto!</b>\n\n"
            "Ora invia la foto che vuoi programmare per questa data e ora.\n\n"
            "<i>📸 Invia la foto come messaggio normale (non come risposta)</i>"
        )
        
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()
        return

    # Selezione ora
    if data.startswith("time_hour_"):
        hour = int(data.split("_")[2])
        
        # Salva ora nel database
        db.save_user_session(user_id=user_id, selected_hour=hour)
        
        text = (
            f"📅 Data selezionata: <b>{selected_date.strftime('%d/%m/%Y')}</b>\n\n"
            f"Ora selezionata: <b>{hour:02d}</b>\n"
            "Seleziona i minuti:"
        )
        
        keyboard = create_time_keyboard(selected_hour=hour, selected_minute=session.get('selected_minute'))
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    # Selezione minuti
    elif data.startswith("time_minute_"):
        minute = int(data.split("_")[2])
        
        # Recupera l'ora
        selected_hour = session.get('selected_hour')
        
        if selected_hour is None:
            await callback.answer("⚠️ Seleziona prima l'ora!", show_alert=True)
            return
        
        # Salva minuti nel database
        db.save_user_session(user_id=user_id, selected_minute=minute)
        
        text = (
            f"� Data selezionata: <b>{selected_date.strftime('%d/%m/%Y')}</b>\n\n"
            f"🕐 Orario: <b>{selected_hour:02d}:{minute:02d}</b>\n\n"
            "Premi <b>Conferma</b> per continuare"
        )
        
        keyboard = create_time_keyboard(selected_hour=selected_hour, selected_minute=minute)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()


@calendar_router.callback_query(F.data == "scheduled_refresh")
async def handle_scheduled_refresh(callback: CallbackQuery):
    """Handler per refresh lista post programmati"""
    user_id = callback.from_user.id
    posts = scheduler.get_user_posts(user_id)

    if not posts:
        await callback.message.edit_text("📭 Non hai post programmati")
        await callback.answer()
        return

    text = "📅 <b>I tuoi post programmati:</b>\n\n"

    for post in posts:
        status_emoji = {
            'scheduled': '⏰',
            'published': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(post.get('status'), '❓')

        scheduled_str = post['scheduled_time'].strftime('%d/%m/%Y %H:%M')
        text += f"{status_emoji} {scheduled_str}\n"

        if post.get('status') == 'published' and post.get('instagram_media_id'):
            text += f"   📸 Media ID: {post['instagram_media_id']}\n"
        elif post.get('status') == 'failed' and post.get('error_message'):
            error_msg = post['error_message'][:50]
            text += f"   ❌ Errore: {error_msg}...\n"

        text += "\n"

    # Keyboard per gestire i post
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Aggiorna", callback_data="scheduled_refresh")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()