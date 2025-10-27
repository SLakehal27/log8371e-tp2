import uuid
from locust import HttpUser, task, between
import json
import time

class KeycloakUser(HttpUser):
    wait_time = between(1,5)
    realm = "master"

    def on_start(self):
        self.token_expires_at = 0
        self.get_keycloak_token()

    def get_keycloak_token(self):
        tokenResponse = self.client.post(
            "/realms/master/protocol/openid-connect/token",
            data={
                "username" : "ralph",
                "password" : "123",
                "grant_type": "password",
                "client_id": "admin-cli",
            }
        )
        if (tokenResponse.status_code != 200):
            print(f"Unable to retrieve token, recieved {tokenResponse.status_code} : {tokenResponse.text}")
            self.environment.runner.quit()
        
        response_data = json.loads(tokenResponse.text)
        self.client.headers["Authorization"] = "Bearer " + response_data['access_token']
        
        # Calculate when the token expires
        expires_in = response_data.get('expires_in', 60)
        self.token_expires_at = time.time() + expires_in - 5

    def ensure_valid_token(self):
        
        if time.time() >= self.token_expires_at:
            self.get_keycloak_token()
    
    @task
    def create_user(self):
        self.ensure_valid_token()
        user_id = f"test__user_{uuid.uuid4()}"

        user_data = {
            "username": user_id,
            "credentials": [{
                "type": "password",
                "value": "Test@123456",
                "temporary": False
            }]
        }

        with self.client.post(
            f"/admin/realms/{self.realm}/users",
            json=user_data,
            name="[CREATE] Create User",
            catch_response=True
            ) as response:
                if response.status_code == 201:
                    response.success()
                elif response.status_code == 409:
                    response.success()
                else:
                    response.failure(f"Failed to create user: {response.status_code} {response.text}")

    @task
    def create_client(self):
        self.ensure_valid_token()
        client_id = f"test_client_{uuid.uuid4()}"
        
        client_data = {
            "clientId": client_id,
        }
        
        with self.client.post(
            f"/admin/realms/{self.realm}/clients",
            json=client_data,
            name="[CREATE] Create Client",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"Failed to create client: {response.status_code} {response.text}")

    @task
    def create_realm_role(self):
        self.ensure_valid_token()
        role_name = f"test_role_{uuid.uuid4()}"
        
        role_data = {
            "name": role_name,
        }
        
        with self.client.post(
            f"/admin/realms/{self.realm}/roles",
            json=role_data,
            name="[CREATE] Create Realm Role",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"Failed to create role: {response.status_code} {response.text}")
    
    @task
    def create_group(self):
        self.ensure_valid_token()
        group_name = f"test_group_{uuid.uuid4()}"
        
        group_data = {
            "name": group_name,
        }
        
        with self.client.post(
            f"/admin/realms/{self.realm}/groups",
            json=group_data,
            name="[CREATE] Create Group",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"Failed to create group: {response.status_code} {response.text}")

    @task
    def create_client_scope(self):
        self.ensure_valid_token()
        scope_name = f"test_scope_{uuid.uuid4()}"
        
        scope_data = {
            "name": scope_name,
            "protocol": "openid-connect"
        }
        
        with self.client.post(
            f"/admin/realms/{self.realm}/client-scopes",
            json=scope_data,
            name="[CREATE] Create Client Scope",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"Failed to create client scope: {response.status_code} {response.text}")