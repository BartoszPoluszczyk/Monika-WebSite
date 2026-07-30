from django.shortcuts import render


def home(request):
    return render(request, "main/home.html")


def about(request):
    context = {
        "title": "O mnie",
        "description": """
            Jestem Monika, dyplomowany dietetyk. Jestem bardzo słodka, choć nie spożywam cukru.
            Tobie, drogi Czytelniku, również tego odradzam, jeśli nie chcesz mieć paskudnych zmian skórnych na plecach.
            Bartosz dość późno sięgnął po rozum do głowy, toteż jego plecy idealnie jeszcze się nie prezentują.
            Jeśli i Ty chcesz mieć piękne i gładkie plecy, skontaktuj się ze mną.
        """,
        "specializations": [
            "Suplementacja",
            "Redukcja masy ciała",
            "Dieta dobierana do indywidualnych potrzeb",
        ],
    }

    return render(request, "main/about.html", context)