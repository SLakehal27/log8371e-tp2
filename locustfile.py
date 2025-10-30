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
                "username" : "admin",
                "password" : "password",
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
    def user_endpoint(self):
        self.ensure_valid_token()
        user_name = f"test__user_{uuid.uuid4()}"
        user_id = ""
        user_data = {
            "username": user_name,
            "enabled": True,
            "credentials": [{
                "type": "password",
                "value": "Test@123456",
                "temporary": False
            }]
        }
        # Create User
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
                    
        # Get user ID
        with self.client.get(
            f"/admin/realms/{self.realm}/users",
            params={"username": user_name},
            name="[READ] Get User ID",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                users = response.json()
                if users:
                    user_id = users[0]["id"]
                    response.success()
                else:
                    response.failure(f"No user found with username {user_name}")
            else:
                response.failure(f"Failed to search for user: {response.status_code} {response.text}")
    
        # Update User
        updated_user_data = {
            "firstName": "Test"}
        with self.client.put(
            f"/admin/realms/{self.realm}/users/{user_id}",
            json=updated_user_data,
            name="[UPDATE] Update User",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to update user: {response.status_code} {response.text}")
                
        # Delete User
        with self.client.delete(
            f"/admin/realms/{self.realm}/users/{user_id}",
            name="[DELETE] Delete User",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to delete user: {response.status_code} {response.text}")

                
    @task
    def client_endpoint(self):
        self.ensure_valid_token()
        client_id = f"test_client_{uuid.uuid4()}"
        
        client_data = {
            "clientId": client_id,
        }
        client_uuid = ""
        
        # Create Client
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
                
        # Get Client ID
        with self.client.get(
            f"/admin/realms/{self.realm}/clients",
            params={"clientId": client_id},
            name="[READ] Get Client ID",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                clients = response.json()
                if clients:
                    client_uuid = clients[0]["id"]
                    response.success()
                else:
                    response.failure(f"No client found with clientId {client_id}")
            else:
                response.failure(f"Failed to search for client: {response.status_code} {response.text}")
                
        # Update Client
        updated_client_data = {
            "name": "Updated Test Client"
        }

        with self.client.put(
            f"/admin/realms/{self.realm}/clients/{client_uuid}",
            json=updated_client_data,
            name="[UPDATE] Update Client",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to update client: {response.status_code} {response.text}")
                
        # Delete Client
        with self.client.delete(
            f"/admin/realms/{self.realm}/clients/{client_uuid}",
            name="[DELETE] Delete Client",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to delete client: {response.status_code} {response.text}")

    @task
    def realm_endpoint(self):
        self.ensure_valid_token()
        role_name = f"test_role_{uuid.uuid4()}"
        
        role_data = {
            "name": role_name,
        }
        
        # Create Realm Role
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
                
        # Get Realm Role name
        with self.client.get(
            f"/admin/realms/{self.realm}/roles/{role_name}",
            name="[READ] Get Realm Role",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get role: {response.status_code} {response.text}")
        
        # Update Realm Role
        updated_role_data = {
            "name": role_name,
            "description": "Updated Test Role"
        }
        with self.client.put(
            f"/admin/realms/{self.realm}/roles/{role_name}",
            json=updated_role_data,
            name="[UPDATE] Update Realm Role",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to update role: {response.status_code} {response.text}")
                
        # Delete Realm Role
        with self.client.delete(
            f"/admin/realms/{self.realm}/roles/{role_name}",
            name="[DELETE] Delete Realm Role",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to delete role: {response.status_code} {response.text}")
    
    @task
    def group_endpoint(self):
        self.ensure_valid_token()
        group_name = f"test_group_{uuid.uuid4()}"
        
        group_data = {
            "name": group_name,
        }

        group_id = ""

        # Create Group
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
                
        # Get Group ID
        with self.client.get(
            f"/admin/realms/{self.realm}/groups",
            name="[READ] Get Group ID",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                groups = response.json()
                group_id = None
                for group in groups:
                    if group["name"] == group_name:
                        group_id = group["id"]
                        break
                if group_id:
                    response.success()
                else:
                    response.failure(f"No group found with name {group_name}")
            else:
                response.failure(f"Failed to get groups: {response.status_code} {response.text}")
        
        # Update Group
        updated_group_data = {
            "name": f"updated_{group_name}",
        }
        with self.client.put(
            f"/admin/realms/{self.realm}/groups/{group_id}",
            json=updated_group_data,
            name="[UPDATE] Update Group",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to update group: {response.status_code} {response.text}")
        
        # Delete Group
        with self.client.delete(
            f"/admin/realms/{self.realm}/groups/{group_id}",
            name="[DELETE] Delete Group",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to delete group: {response.status_code} {response.text}")

    @task
    def client_scope_endpoint(self):
        self.ensure_valid_token()
        scope_name = f"test_scope_{uuid.uuid4()}"
        
        scope_data = {
            "name": scope_name,
            "protocol": "openid-connect"
        }

        scope_id = ""
        
        # Create Client Scope
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
                
        # Get Client Scope ID
        with self.client.get(
            f"/admin/realms/{self.realm}/client-scopes",
            name="[READ] Get Client Scope ID",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                scopes = response.json()
                scope_id = None
                for scope in scopes:
                    if scope["name"] == scope_name:
                        scope_id = scope["id"]
                        break
                if scope_id:
                    response.success()
                else:
                    response.failure(f"No client scope found with name {scope_name}")
            else:
                response.failure(f"Failed to get client scopes: {response.status_code} {response.text}")
        
        # Update Client Scope
        updated_scope_data = {
            "name": f"updated_{scope_name}",
            "protocol": "openid-connect"
        }
        with self.client.put(
            f"/admin/realms/{self.realm}/client-scopes/{scope_id}",
            json=updated_scope_data,
            name="[UPDATE] Update Client Scope",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to update client scope: {response.status_code} {response.text}")

        # Delete Client Scope
        with self.client.delete(
            f"/admin/realms/{self.realm}/client-scopes/{scope_id}",
            name="[DELETE] Delete Client Scope",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to delete client scope: {response.status_code} {response.text}")