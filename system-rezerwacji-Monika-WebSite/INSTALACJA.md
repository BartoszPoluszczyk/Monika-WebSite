# System rezerwacji wizyt

Paczka jest przeznaczona do nałożenia na katalog główny projektu `Monika-WebSite`.
Nie zawiera bazy danych ani zdjęć, więc nie usuwa treści dodanych wcześniej w panelu administratora.

## Instalacja

1. Rozpakuj paczkę do katalogu `Monika-WebSite` i zaakceptuj zastąpienie wskazanych plików.
2. W aktywnym środowisku projektu wykonaj:

   ```powershell
   python manage.py migrate
   ```

3. Uruchom stronę ponownie.

Nie są potrzebne żadne nowe biblioteki zewnętrzne.

## Pierwsza konfiguracja w panelu administratora

W sekcji **Rezerwacje**:

1. Otwórz **Godziny pracy** i dodaj przedziały, w których Monika przyjmuje pacjentów.
2. Otwórz **Ustawienia rezerwacji** i określ przerwę między wizytami, minimalne wyprzedzenie i zakres rezerwacji.
3. Urlopy i pojedyncze niedostępne godziny dodawaj w **Zablokowane terminy i dni wolne**. Puste godziny oznaczają blokadę całego dnia.
4. W **Wizyty** dostępna jest lista oraz przycisk **Kalendarz wizyt**.

Wolne terminy są obliczane z czasu trwania usługi, dlatego każda rezerwowalna usługa musi mieć uzupełnione pole **Czas trwania w minutach**.

## Zakres

- publiczny kalendarz dostępnych terminów,
- wybór usługi oraz wizyty online lub stacjonarnej,
- formularz danych kontaktowych,
- zabezpieczenie przed ponownym zajęciem terminu,
- potwierdzenie i samodzielne anulowanie wizyty,
- grafik tygodniowy, przerwy, urlopy i blokady,
- miesięczny kalendarz Moniki w panelu,
- polska strefa czasowa `Europe/Warsaw`,
- testy automatyczne modułu rezerwacji.
