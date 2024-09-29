import pytest
from faker import Faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

base_route = "http://127.0.0.1:8080/users/"

faker = Faker()


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    user_data = {
        "user_in": {
            "name": faker.name(),
            "email": faker.email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "username": "test",
        },
        "company_in": {
            "name": faker.company(),
            "address": faker.address(),
            "email": faker.company_email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "registration_number": faker.numerify("##########"),
        },
    }

    response = await client.post(
        f"{base_route}?password=test&is_admin=true", json=user_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == user_data["user_in"]["name"]
    assert data["email"] == user_data["user_in"]["email"]
    assert data["country_code"] == user_data["user_in"]["country_code"]
    assert data["phone_number"] == user_data["user_in"]["phone_number"]
    assert data["username"] == user_data["user_in"]["username"]
    assert data["id"]


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient):
    user_data = {
        "user_in": {
            "name": faker.name(),
            "email": faker.email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "username": "test",
        },
        "company_in": {
            "name": faker.company(),
            "address": faker.address(),
            "email": faker.company_email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "registration_number": faker.numerify("##########"),
        },
    }

    response = await client.post(
        f"{base_route}?password=test&is_admin=true", json=user_data
    )
    assert response.status_code == 200

    response = await client.get(base_route)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, session: AsyncSession):
    user_data = {
        "user_in": {
            "name": faker.name(),
            "email": faker.email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "username": "test",
        },
        "company_in": {
            "name": faker.company(),
            "address": faker.address(),
            "email": faker.company_email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "registration_number": faker.numerify("##########"),
        },
    }

    response = await client.post(
        f"{base_route}?password=test&is_admin=true", json=user_data
    )
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]

    update_user_data = {"name": "Updated Name"}

    response = await client.put(f"{base_route}{user_id}", json=update_user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_user_data["name"]


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    user_data = {
        "user_in": {
            "name": faker.name(),
            "email": faker.email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "username": "test",
        },
        "company_in": {
            "name": faker.company(),
            "address": faker.address(),
            "email": faker.company_email(),
            "country_code": faker.country_code(),
            "phone_number": faker.numerify("##########"),
            "registration_number": faker.numerify("##########"),
        },
    }

    response = await client.post(
        f"{base_route}?password=test&is_admin=true", json=user_data
    )
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]
    response = await client.delete(f"{base_route}{user_id}")
    assert response.status_code == 200
