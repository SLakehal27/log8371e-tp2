from locust import HttpUser, task, between
import ast

class KeycloakUser(HttpUser):
    wait_time = between(1,5)

    def on_start(self):
        self.get_keycloak_token()

    def get_keycloak_token(self):
        tokenResponse = self.client.post(
            "/realms/master/protocol/openid-connect/token",
            data={
                "username" : "admin",
                "password" : "password",
                "grant_type": "password",
                "client_id": "myclient", # Depends on your client name
                "client_secret": "9ZekauFZlkrk92uvgFO5WYX72Evcwoqa" # Depends on your generated client
            }
        )
        if (tokenResponse.status_code != 200):
            print(f"Unable to retrieve token, recieved {tokenResponse.status_code} : {tokenResponse.text}")
            self.environment.runner.quit()
        self.client.headers["Authorization"] = "Bearer " + ast.literal_eval(tokenResponse.text)['access_token']