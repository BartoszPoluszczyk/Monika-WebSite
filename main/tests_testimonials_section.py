from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .forms import TestimonialSubmissionForm
from .models import Testimonial


class TestimonialModelTests(SimpleTestCase):
    def test_defaults_require_explicit_consent_and_moderation_before_publishing(self):
        testimonial = Testimonial(author_name="Anna K.", content="Świetna współpraca.")

        self.assertTrue(testimonial.is_active)
        self.assertFalse(testimonial.consent_confirmed)
        self.assertEqual(testimonial.status, Testimonial.Status.PENDING)

    def test_star_helpers_split_rating_out_of_five(self):
        testimonial = Testimonial(author_name="Anna K.", content="Polecam.", rating=3)

        self.assertEqual(len(list(testimonial.full_stars)), 3)
        self.assertEqual(len(list(testimonial.empty_stars)), 2)

    def test_star_helpers_handle_missing_rating(self):
        testimonial = Testimonial(author_name="Anna K.", content="Polecam.")

        self.assertEqual(len(list(testimonial.full_stars)), 0)
        self.assertEqual(len(list(testimonial.empty_stars)), 5)


class TestimonialsSectionRenderingTests(SimpleTestCase):
    def render(self, testimonials):
        return render_to_string(
            "main/partials/testimonials.html",
            {"testimonials": testimonials},
        )

    def test_empty_testimonials_render_message_without_carousel(self):
        html = self.render([])

        self.assertIn("Opinie pacjentów pojawią się tutaj wkrótce.", html)
        self.assertNotIn('id="testimonialsCarousel"', html)

    def test_single_testimonial_has_no_controls_or_indicators(self):
        html = self.render([Testimonial(author_name="Anna K.", content="Bardzo profesjonalne podejście.")])

        self.assertIn('id="testimonialsCarousel"', html)
        self.assertEqual(html.count('class="carousel-item active"'), 1)
        self.assertNotIn("carousel-indicators", html)
        self.assertNotIn("carousel-control-prev", html)
        self.assertNotIn("carousel-control-next", html)

    def test_multiple_testimonials_render_indicators_and_controls(self):
        testimonials = [
            Testimonial(author_name="Anna K.", content="Opinia pierwsza"),
            Testimonial(author_name="Basia W.", content="Opinia druga"),
            Testimonial(author_name="Celina R.", content="Opinia trzecia"),
        ]

        html = self.render(testimonials)

        self.assertEqual(html.count('class="testimonial-card"'), 3)
        self.assertEqual(html.count('class="carousel-item active"'), 1)
        self.assertEqual(html.count('data-bs-slide-to='), 3)
        self.assertIn("carousel-control-prev", html)
        self.assertIn("carousel-control-next", html)
        self.assertLess(html.index("Anna K."), html.index("Celina R."))

    def test_rating_renders_filled_and_empty_stars(self):
        html = self.render([Testimonial(author_name="Anna K.", content="Super.", rating=4)])

        self.assertEqual(html.count('class="star star-filled"'), 4)
        self.assertEqual(html.count('class="star star-empty"'), 1)

    def test_testimonial_without_rating_hides_stars(self):
        html = self.render([Testimonial(author_name="Anna K.", content="Super.")])

        self.assertNotIn("testimonial-rating", html)

    def test_testimonial_content_stays_escaped(self):
        html = self.render([
            Testimonial(
                author_name='<script>alert("author")</script>',
                content='<img src=x onerror="alert(1)">',
            ),
        ])

        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;img", html)


class TestimonialsHomeViewTests(TestCase):
    def test_home_only_shows_active_consented_and_approved_testimonials(self):
        Testimonial.objects.create(
            author_name="Widoczna Wanda",
            content="Zgodziłam się na publikację.",
            is_active=True,
            consent_confirmed=True,
            status=Testimonial.Status.APPROVED,
        )
        Testimonial.objects.create(
            author_name="Bez Zgody Barbara",
            content="Nie zgodziłam się na publikację.",
            is_active=True,
            consent_confirmed=False,
            status=Testimonial.Status.APPROVED,
        )
        Testimonial.objects.create(
            author_name="Ukryta Urszula",
            content="Zgoda jest, ale wpis wyłączony.",
            is_active=False,
            consent_confirmed=True,
            status=Testimonial.Status.APPROVED,
        )
        Testimonial.objects.create(
            author_name="Oczekująca Ola",
            content="Zgłoszona, ale jeszcze nie sprawdzona.",
            is_active=True,
            consent_confirmed=True,
            status=Testimonial.Status.PENDING,
        )
        Testimonial.objects.create(
            author_name="Odrzucona Renata",
            content="Nie przeszła moderacji.",
            is_active=True,
            consent_confirmed=True,
            status=Testimonial.Status.REJECTED,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Widoczna Wanda")
        self.assertNotContains(response, "Bez Zgody Barbara")
        self.assertNotContains(response, "Ukryta Urszula")
        self.assertNotContains(response, "Oczekująca Ola")
        self.assertNotContains(response, "Odrzucona Renata")

    def test_home_links_to_the_submission_page(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("submit_testimonial"))


class TestimonialSubmissionFormTests(SimpleTestCase):
    def test_valid_submission_requires_consent(self):
        form = TestimonialSubmissionForm(data={
            "author_name": "Anna K.",
            "content": "Bardzo profesjonalne podejście.",
            "rating": "5",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("consent_confirmed", form.errors)

    def test_valid_submission_with_consent_passes(self):
        form = TestimonialSubmissionForm(data={
            "author_name": "Anna K.",
            "content": "Bardzo profesjonalne podejście.",
            "rating": "5",
            "consent_confirmed": "on",
        })

        self.assertTrue(form.is_valid())

    def test_rating_is_optional(self):
        form = TestimonialSubmissionForm(data={
            "author_name": "Anna K.",
            "content": "Bardzo profesjonalne podejście.",
            "consent_confirmed": "on",
        })

        self.assertTrue(form.is_valid())


class SubmitTestimonialViewTests(TestCase):
    def test_get_renders_empty_form(self):
        response = self.client.get(reverse("submit_testimonial"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Podziel się")

    def test_valid_post_creates_pending_testimonial_and_redirects(self):
        response = self.client.post(reverse("submit_testimonial"), data={
            "author_name": "Anna K.",
            "content": "Bardzo profesjonalne podejście, polecam.",
            "rating": "5",
            "consent_confirmed": "on",
        })

        self.assertRedirects(response, f"{reverse('submit_testimonial')}?wyslano=1")
        testimonial = Testimonial.objects.get(author_name="Anna K.")
        self.assertEqual(testimonial.status, Testimonial.Status.PENDING)
        self.assertTrue(testimonial.consent_confirmed)

    def test_submission_without_consent_is_not_saved(self):
        self.client.post(reverse("submit_testimonial"), data={
            "author_name": "Anna K.",
            "content": "Bardzo profesjonalne podejście.",
            "rating": "5",
        })

        self.assertFalse(Testimonial.objects.exists())

    def test_thank_you_message_shown_after_redirect(self):
        response = self.client.get(f"{reverse('submit_testimonial')}?wyslano=1")

        self.assertContains(response, "Dziękujemy")
