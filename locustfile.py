from locust import HttpUser, task, between, SequentialTaskSet
from locust.exception import StopUser
import ast
import uuid

class SequentialKeycloakTasks(SequentialTaskSet):
    client_ids = [str(uuid.uuid4()) for i in range(5)]

    def regenerate_client_ids(self):
        self.client_ids = [str(uuid.uuid4()) for i in range(5)]

    @task
    def get_keycloak_token(self):
        tokenResponse = self.client.post(
            "/realms/master/protocol/openid-connect/token",
            data={
                "username" : "admin",
                "password" : "password",
                "grant_type": "password",
                "client_id": "myclient", # Depends on your custom client name
                "client_secret": "" # Replace with your Keycloak client's secret
            }
        )
        if (tokenResponse.status_code != 200):
            print(f"Unable to retrieve token, recieved {tokenResponse.status_code} : {tokenResponse.text}")
            self.environment.runner.quit()
        self.client.headers["Authorization"] = "Bearer " + ast.literal_eval(tokenResponse.text)['access_token']
        
    @task
    def create_clients(self):
        self.regenerate_client_ids()
        for id in self.client_ids:
            clientResponse = self.client.post("/admin/realms/master/clients", json= {
                "id": id
            })

            if clientResponse.status_code != 201:
                print(f"Unable to create new client, recieved {clientResponse.status_code} : {clientResponse.text}")
                raise StopUser()
            # print(f"User {id} created!")
    
    @task
    def delete_clients(self):
        for id in self.client_ids:
            clientResponse = self.client.delete(f"/admin/realms/master/clients/{id}")

            if clientResponse.status_code != 204:
                print(f"Unable to delete client {id}, recieved {clientResponse.status_code} : {clientResponse.text}")
                raise StopUser()
            # print(f"User {id} deleted!")
    
    @task
    def done(self):
        raise StopUser()


class KeycloakUser(HttpUser):
    wait_time = between(1,5)
    tasks = [SequentialKeycloakTasks]