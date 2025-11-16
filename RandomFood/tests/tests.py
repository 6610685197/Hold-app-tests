from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.contrib import admin
from RandomFood.models import Food, FoodCategory, FoodType
from accounts.models import UserProfile
import json


class RandomFoodModelsTest(TestCase):
    def setUp(self):
        self.category = FoodCategory.objects.create(name="Dessert")
        self.type1 = FoodType.objects.create(name="Sweet")
        self.food = Food.objects.create(
            name="Ice Cream",
            category=self.category,
            favorite_count=0,
        )
        self.food.food_types.add(self.type1)

    def test_food_str(self):
        self.assertEqual(str(self.food), "Ice Cream")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Dessert")

    def test_food_type_str(self):
        self.assertEqual(str(self.type1), "Sweet")

    def test_food_food_types_relation(self):
        self.assertIn(self.type1, self.food.food_types.all())


class RandomFoodViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.profile = UserProfile.objects.create(user=self.user)
        self.category = FoodCategory.objects.create(name="Dessert")
        self.type1 = FoodType.objects.create(name="Sweet")
        self.food = Food.objects.create(
            name="Ice Cream",
            category=self.category,
            favorite_count=0,
        )
        self.food.food_types.add(self.type1)

    # ทดสอบหน้า HTML หลัก random_food_page
    def test_random_food_page(self):
        response = self.client.get(reverse("random_food_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "RandomFood/home.html")
        self.assertIn("categories", response.context)
        self.assertIn("types", response.context)

    def test_api_random_food_batch_default(self):
        response = self.client.get(reverse("api_random_food_batch"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("cards", data)
        self.assertIn("done", data)
        self.assertTrue(len(data["cards"]) >= 1)

    def test_api_random_food_batch_with_params(self):
        response = self.client.get(
            reverse("api_random_food_batch"),
            {"category": self.category.id, "types": str(self.type1.id), "n": 1},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["cards"]), 1)
        self.assertEqual(data["cards"][0]["id"], self.food.pk)

    def test_add_favorite_requires_login(self):
        response = self.client.post(reverse("remove_favorite", args=[self.food.pk]))
        self.assertEqual(response.status_code, 302)  # redirects to login

    def test_api_add_favorite_post(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            reverse("api_add_favorite"),
            data=json.dumps({"food_id": self.food.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "added")
        profile = UserProfile.objects.get(user=self.user)
        self.assertIn(self.food, profile.favorites.all())

    def test_api_get_favorites(self):
        self.client.login(username="testuser", password="12345")
        profile = self.profile
        profile.favorites.add(self.food)
        response = self.client.get(reverse("api_get_favorites"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["favorites"]), 1)
        self.assertEqual(data["favorites"][0]["id"], self.food.pk)

    def test_remove_favorite(self):
        self.client.login(username="testuser", password="12345")
        profile = self.profile
        profile.favorites.add(self.food)
        response = self.client.get(reverse("remove_favorite", args=[self.food.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        profile.refresh_from_db()
        self.assertNotIn(self.food, profile.favorites.all())


class RandomFoodURLsTest(TestCase):
    def test_urls_resolve(self):
        self.assertEqual(resolve("/").func.__name__, "random_food_page")
        self.assertEqual(
            resolve("/api/foods/batch/").func.__name__, "api_random_food_batch"
        )
        self.assertEqual(
            resolve("/api/favorites/add/").func.__name__, "api_add_favorite"
        )
        self.assertEqual(resolve("/api/favorites/").func.__name__, "api_get_favorites")
        self.assertEqual(
            resolve("/remove-favorite/1/").func.__name__, "remove_favorite"
        )


class RandomFoodAdminTest(TestCase):
    def test_admin_registration(self):

        # Check if models are registered
        self.assertIn(Food, admin.site._registry)
        self.assertIn(FoodCategory, admin.site._registry)
        self.assertIn(FoodType, admin.site._registry)
