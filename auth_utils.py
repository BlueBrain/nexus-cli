from keycloak import KeycloakOpenID


def get_auth_server():
    return KeycloakOpenID(server_url="https://bbpteam.epfl.ch/auth/",
                          realm_name='BBP',
                          client_id='bbp-nexus-production',
                          client_secret_key='3feeed86-b6d6-4d87-b825-a792c28780b8')