# Monika-WebSite

Strona gabinetu dietetycznego Moniki: oferta, rezerwacje, płatności Stripe, newsletter i opinie.

## Uruchomienie lokalne

```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

Po migracji uzupełnij w panelu:

1. **MAIN → Ustawienia strony** — dane działalności używane w dokumentach.
2. **MAIN → Dokumenty prawne** — regulamin, politykę prywatności i cookies.
3. **REZERWACJE → Ustawienia rezerwacji** — zasady terminów i powiadomień.

Wbudowane dokumenty są wersją roboczą i przed publikacją wymagają weryfikacji zgodnie z faktycznym statusem działalności i usług Moniki.

## Konfiguracja produkcyjna

Wartości z `.env.example` ustaw w panelu hostingu. Projekt nie wczytuje pliku `.env` automatycznie.

Na serwerze ustaw co najmniej `DJANGO_DEBUG=false`, losowy `DJANGO_SECRET_KEY`, domenę w `DJANGO_ALLOWED_HOSTS`, adres HTTPS w `DJANGO_CSRF_TRUSTED_ORIGINS`, klucze Stripe, pocztę i `BOOKING_SITE_URL`.

```powershell
py manage.py check --deploy
py manage.py migrate
py manage.py collectstatic --noinput
py manage.py test
```
