from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
import json


class TestAPIRoot(TestCase):
    def test_welcome(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profiles/")

    def test_profiles(self):
        response = self.client.get("/profiles/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            b'"Welcome to The Wall API! Usage: profiles/upload/ - to upload data file; profiles/raw/ - to see raw db data; profiles/overview - to see total cost for all profiles; profiles/overview/<day_no> - to see the costs for up to a given day for all profiles; profiles/<profile_no>/overview/<day_no> - to see the costs for up to a given day for a given profile; profiles/<profile_no>/days/<day_no> - to see the amount of ice for a given day for a given profile"',
        )


class TestAPIUpload(TestCase):
    def test_upload_get(self):
        response = self.client.get("/profiles/upload/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'"Use POST request to upload data file"')

    def test_upload_file(self):
        with open("sample_input.txt", "rb") as file:
            uploaded_file = SimpleUploadedFile("file_uploaded", file.read())

        response = self.client.post(
            "/profiles/upload/",
            {"file_uploaded": uploaded_file, "workers": 1},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'"File upload successful!"')

    def test_upload_file_more_workers(self):
        with open("sample_input.txt", "rb") as file:
            uploaded_file = SimpleUploadedFile("file_uploaded", file.read())

        response = self.client.post(
            "/profiles/upload/",
            {"file_uploaded": uploaded_file, "workers": 5},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'"File upload successful!"')

    def test_upload_post_no_file(self):
        response = self.client.post("/profiles/upload/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content,
            b'"File upload failed: No file uploaded!"',
        )

    def test_upload_post_no_workers(self):
        with open("sample_input.txt", "rb") as file:
            uploaded_file = SimpleUploadedFile("file_uploaded", file.read())

        response = self.client.post(
            "/profiles/upload/",
            {"file_uploaded": uploaded_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'"File upload successful!"')


class TestAPIProfilesSingleThread(TestCase):
    def setUp(self) -> None:
        with open("sample_input.txt", "rb") as file:
            uploaded_file = SimpleUploadedFile("file_uploaded", file.read())

        self.client.post(
            "/profiles/upload/",
            {"file_uploaded": uploaded_file},
            format="multipart",
        )

    def test_overview(self):
        response = self.client.get("/profiles/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"day": None, "cost": 32233500},
        )

    def test_overview_day_1(self):
        response = self.client.get("/profiles/overview/1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"day": 1, "cost": 3334500},
        )

    def test_overview_day_1_profile_1(self):
        response = self.client.get("/profiles/1/overview/1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"day": 1, "cost": 1111500},
        )

    def test_profile_1_day_1(self):
        response = self.client.get("/profiles/1/days/1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"day": 1, "ice_amount": 585},
        )


class TestAPIProfilesMultiThread(TestAPIProfilesSingleThread):
    def setUp(self) -> None:
        with open("sample_input.txt", "rb") as file:
            uploaded_file = SimpleUploadedFile("file_uploaded", file.read())

        self.client.post(
            "/profiles/upload/",
            {"file_uploaded": uploaded_file, "workers": 5},
            format="multipart",
        )

    def test_overview_day_1(self):
        response = self.client.get("/profiles/overview/1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"day": 1, "cost": 1852500},
        )

    def test_overview(self):
        response = self.client.get("/profiles/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"day": None, "cost": 15561000},
        )
