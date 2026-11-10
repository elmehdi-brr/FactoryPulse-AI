
from httpx import AsyncClient


ROLE_NAMES = ("admin", "manager", "technician", "operator")
MANAGEMENT_ROLE_NAMES = {"admin", "manager"}


async def create_base_hierarchy(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> dict[str, int]:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "RBAC Base Organization",
            "code": "RBAC-BASE-ORG",
            "description": "Hierarchy RBAC tests",
        },
    )
    assert organization_response.status_code == 201, organization_response.text
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "RBAC Base Site",
            "code": "RBAC-BASE-SITE",
            "location": "Test Location",
            "description": "Hierarchy RBAC tests",
        },
    )
    assert site_response.status_code == 201, site_response.text
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "RBAC Base Area",
            "code": "RBAC-BASE-AREA",
            "description": "Hierarchy RBAC tests",
        },
    )
    assert area_response.status_code == 201, area_response.text
    area = area_response.json()

    line_response = await client.post(
        "/production-lines",
        headers=admin_headers,
        json={
            "area_id": area["id"],
            "name": "RBAC Base Line",
            "code": "RBAC-BASE-LINE",
            "description": "Hierarchy RBAC tests",
        },
    )
    assert line_response.status_code == 201, line_response.text
    production_line = line_response.json()

    return {
        "organization_id": organization["id"],
        "site_id": site["id"],
        "area_id": area["id"],
        "production_line_id": production_line["id"],
    }


async def get_resource_codes(
    client: AsyncClient,
    admin_headers: dict[str, str],
    endpoint: str,
) -> set[str]:
    response = await client.get(
        endpoint,
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text

    return {
        item["code"]
        for item in response.json()
    }


# =========================================================
# ORGANIZATION RBAC
# =========================================================


async def test_organization_creation_requires_management_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    for role_name in ROLE_NAMES:
        code = f"RBAC-ORG-{role_name.upper()}"

        response = await client.post(
            "/organizations",
            headers=auth_headers[role_name],
            json={
                "name": f"Organization {role_name}",
                "code": code,
                "description": "Organization RBAC test",
            },
        )

        expected_status = (
            201 if role_name in MANAGEMENT_ROLE_NAMES else 403
        )
        assert response.status_code == expected_status, response.text

    codes = await get_resource_codes(
        client,
        auth_headers["admin"],
        "/organizations",
    )

    assert "RBAC-ORG-ADMIN" in codes
    assert "RBAC-ORG-MANAGER" in codes
    assert "RBAC-ORG-TECHNICIAN" not in codes
    assert "RBAC-ORG-OPERATOR" not in codes


# =========================================================
# SITE RBAC
# =========================================================


async def test_site_creation_requires_management_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    for role_name in ROLE_NAMES:
        code = f"RBAC-SITE-{role_name.upper()}"

        response = await client.post(
            "/sites",
            headers=auth_headers[role_name],
            json={
                "organization_id": hierarchy["organization_id"],
                "name": f"Site {role_name}",
                "code": code,
                "location": "Test Location",
                "description": "Site RBAC test",
            },
        )

        expected_status = (
            201 if role_name in MANAGEMENT_ROLE_NAMES else 403
        )
        assert response.status_code == expected_status, response.text

    codes = await get_resource_codes(
        client,
        auth_headers["admin"],
        "/sites",
    )

    assert "RBAC-SITE-ADMIN" in codes
    assert "RBAC-SITE-MANAGER" in codes
    assert "RBAC-SITE-TECHNICIAN" not in codes
    assert "RBAC-SITE-OPERATOR" not in codes


# =========================================================
# AREA RBAC
# =========================================================


async def test_area_creation_requires_management_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    for role_name in ROLE_NAMES:
        code = f"RBAC-AREA-{role_name.upper()}"

        response = await client.post(
            "/areas",
            headers=auth_headers[role_name],
            json={
                "site_id": hierarchy["site_id"],
                "name": f"Area {role_name}",
                "code": code,
                "description": "Area RBAC test",
            },
        )

        expected_status = (
            201 if role_name in MANAGEMENT_ROLE_NAMES else 403
        )
        assert response.status_code == expected_status, response.text

    codes = await get_resource_codes(
        client,
        auth_headers["admin"],
        "/areas",
    )

    assert "RBAC-AREA-ADMIN" in codes
    assert "RBAC-AREA-MANAGER" in codes
    assert "RBAC-AREA-TECHNICIAN" not in codes
    assert "RBAC-AREA-OPERATOR" not in codes


# =========================================================
# PRODUCTION LINE RBAC
# =========================================================


async def test_production_line_creation_requires_management_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    for role_name in ROLE_NAMES:
        code = f"RBAC-LINE-{role_name.upper()}"

        response = await client.post(
            "/production-lines",
            headers=auth_headers[role_name],
            json={
                "area_id": hierarchy["area_id"],
                "name": f"Production Line {role_name}",
                "code": code,
                "description": "Production line RBAC test",
            },
        )

        expected_status = (
            201 if role_name in MANAGEMENT_ROLE_NAMES else 403
        )
        assert response.status_code == expected_status, response.text

    codes = await get_resource_codes(
        client,
        auth_headers["admin"],
        "/production-lines",
    )

    assert "RBAC-LINE-ADMIN" in codes
    assert "RBAC-LINE-MANAGER" in codes
    assert "RBAC-LINE-TECHNICIAN" not in codes
    assert "RBAC-LINE-OPERATOR" not in codes


# =========================================================
# HIERARCHY UPDATE RBAC
# =========================================================


async def test_hierarchy_updates_require_management_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    resources = (
        (
            "organization",
            f"/organizations/{hierarchy['organization_id']}",
            "RBAC Base Organization",
        ),
        (
            "site",
            f"/sites/{hierarchy['site_id']}",
            "RBAC Base Site",
        ),
        (
            "area",
            f"/areas/{hierarchy['area_id']}",
            "RBAC Base Area",
        ),
        (
            "production line",
            f"/production-lines/{hierarchy['production_line_id']}",
            "RBAC Base Line",
        ),
    )

    for resource_name, endpoint, original_name in resources:
        current_name = original_name

        for role_name in ROLE_NAMES:
            updated_name = f"{resource_name} updated by {role_name}"

            response = await client.patch(
                endpoint,
                headers=auth_headers[role_name],
                json={"name": updated_name},
            )

            expected_status = (
                200 if role_name in MANAGEMENT_ROLE_NAMES else 403
            )
            assert response.status_code == expected_status, response.text

            resource_after = await client.get(
                endpoint,
                headers=auth_headers["admin"],
            )
            assert resource_after.status_code == 200, resource_after.text

            if role_name in MANAGEMENT_ROLE_NAMES:
                current_name = updated_name

            assert resource_after.json()["name"] == current_name, (
                f"{resource_name} was unexpectedly modified by "
                f"{role_name}"
            )


# =========================================================
# HIERARCHY READ RBAC
# =========================================================


async def test_hierarchy_reads_are_available_to_all_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    resources = (
        (
            "/organizations",
            f"/organizations/{hierarchy['organization_id']}",
            hierarchy["organization_id"],
        ),
        (
            "/sites",
            f"/sites/{hierarchy['site_id']}",
            hierarchy["site_id"],
        ),
        (
            "/areas",
            f"/areas/{hierarchy['area_id']}",
            hierarchy["area_id"],
        ),
        (
            "/production-lines",
            f"/production-lines/{hierarchy['production_line_id']}",
            hierarchy["production_line_id"],
        ),
    )

    for role_name in ROLE_NAMES:
        for collection_endpoint, detail_endpoint, resource_id in resources:
            collection_response = await client.get(
                collection_endpoint,
                headers=auth_headers[role_name],
            )
            assert collection_response.status_code == 200, (
                collection_response.text
            )

            returned_ids = {
                item["id"]
                for item in collection_response.json()
            }
            assert resource_id in returned_ids

            detail_response = await client.get(
                detail_endpoint,
                headers=auth_headers[role_name],
            )
            assert detail_response.status_code == 200, (
                detail_response.text
            )
            assert detail_response.json()["id"] == resource_id
