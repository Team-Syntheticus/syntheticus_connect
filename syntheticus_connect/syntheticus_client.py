import requests
import json
import logging
import os
from datetime import datetime
from tabulate import tabulate

class syntheticus_client:
    """
    A class for interacting with the Syntheticus API.
    """
    def _authorized_headers(self):
        """
        Get the authorized headers including the authentication token.

        Returns:
            dict: The headers dictionary.
        """
        return {
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json'
                }

    def __init__(self, host):
        """
        Initialize the SyntheticusConnect instance.

        Args:
            host (str): The base URL of the API.
        """
        self.host = host + ':8000'
        self.host_airflow = host + ':8080'
        self.token = None
        self.user = None
        self.password = None
        self.projects = {}
        self.session = requests.Session()
        #self.session.auth = (self.user, self.password)
        self.session.auth = ('airflow', 'airflow')
        self.main_data_dir = './media/'
        self.project_id = None
        self.dag_id = None  
        self.dataset_id = None

    def register(self, username, email, password):
        """
        Register a new user.

        Args:
            username (str): The username for the new user.
            email (str): The email address for the new user.
            password (str): The password for the new user.

        Returns:
            dict: The response JSON containing the registration details.
        """
        url = f"{self.host}/dj-rest-auth/registration/"
        body = {
            "username": username,
            "email": email,
            "password1": password,
            "password2": password
        }
        response = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
        return response.json() # do not show the key

    def login(self, username, password):
        """
        Log in to the API.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.

        Returns:
            str: The login status message.
        """
        self.user = username
        self.password = password
        url = f"{self.host}/dj-rest-auth/login/"
        body = {
            "username": username,
            "password": password
        }
        response = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            self.token = response.json().get('key')  
            return "Login successful."
        else:
            return f"Login failed. Status code: {response.status_code}"

    def logout(self):
        """
        Log out from the API.

        Returns:
            str: The response text from the logout request.
        """
        url = f"{self.host}/dj-rest-auth/logout/"
        response = requests.post(url, headers=self._authorized_headers())
        return response.text

    def change_password(self, new_password):
        """
        Change the user's password.

        Args:
            new_password (str): The new password.

        Returns:
            dict: The response JSON containing the password change details.
        """
        url = f"{self.host}/dj-rest-auth/password/change/"
        body = {
            "new_password1": new_password,
            "new_password2": new_password
        }
        response = requests.post(url, data=json.dumps(body), headers=self._authorized_headers())
        return response.json()

    def get_user(self, user_id):
        """
        Get user details by user ID.

        Args:
            user_id (str): The ID of the user.

        Returns:
            str: The response text containing the user details.
        """
        url = f"{self.host}/api/users/{user_id}/"
        response = requests.get(url, headers=self._authorized_headers())
        return response.text

    def get_me(self):
        """
        Get the current user's details.

        Returns:
            None
        """
        url = f"{self.host}/api/users/me/"
        response = requests.get(url, headers=self._authorized_headers())
        if response.status_code == 200:
            user_data = response.json()
            username = user_data.get('username')
            name = user_data.get('name')
            user_url = user_data.get('url')

            print("User details:")
            print(f"Username: {username}")
            print(f"Name: {name}")
            print(f"URL: {user_url}")
            print("-" * 20)
        else:
            print("Error fetching user details.")

    def create_project(self, name):
        """
        Create a new project.

        Args:
            name (str): The name of the project.

        Returns:
            dict: The response JSON containing the project details.
        """
        url = f"{self.host}/api/projects/"
        body = {
            "name": name
        }
        response = requests.post(url, data=json.dumps(body), headers=self._authorized_headers())
        if response.status_code == 201:
            project_data = response.json()
            project_id = project_data.get('id')
            project_name = project_data.get('name')
            created_at = project_data.get('created_at')

            print("Project created:")
            print(f"ID: {project_id}")
            print(f"Name: {project_name}")
            print(f"Created at: {created_at}")
            print("-" * 20)

            self.projects[project_id] = project_name
        else:
            print('Error creating the project.')

    def get_projects(self):
        """
        Get the list of projects.

        Returns:
            None
        """
        url = f"{self.host}/api/projects/"
        response = requests.get(url, headers=self._authorized_headers())
        if response.status_code == 200:
            projects_data = response.json().get('results', [])
            if projects_data:
                # Prepare data for table
                table_data = []
                for project in projects_data:
                    row = [
                        project.get('id'),
                        project.get('name'),
                        project.get('created_at'),
                    ]
                    table_data.append(row)

                # Define table headers
                headers = ['Project ID', 'Project Name', 'Created At']

                # Print table
                print("Projects:")
                print(tabulate(table_data, headers=headers, tablefmt='pretty'))
            else:
                print("No projects found.")
        else:
            print("Error fetching projects.")

    def get_datasets(self, project_id):
        """
        List the dataset folders for a project.

        Args:
            project_id (str): The ID of the project.

        Returns:
            dict: The response JSON containing the dataset folders.
        """
        url = f"{self.host}/api/projects/{project_id}/list-dataset-folders/"

        payload = {}
        files = {}
        headers = {
        'Authorization': f'Token {self.token}'
        }

        response = requests.request("GET", url, headers=headers, data=payload, files=files)
        data = json.loads(response.text)

        # Prepare data for table
        table_data = []
        for result in data.get('results', []):
            for outer_dataset in result.get('datasets', []):
                for dataset in outer_dataset.get('datasets', []):
                    row = [
                        dataset.get('dataset_name'),
                        dataset.get('id'),
                        result.get('project'),
                        result.get('data_type'),
                        dataset.get('size'),
                        dataset.get('rows_number'),
                        len(dataset.get('dataset_metadata', {}).get('column_types', {}))
                    ]
                    table_data.append(row)

        # Define table headers
        headers = ['Dataset Name', 'Dataset ID', 'Project ID', 'Data Type', 'Size', 'Number of Rows', 'Number of Columns']

        # Print table
        print(tabulate(table_data, headers=headers, tablefmt='pretty'))


    def delete_project(self, project_id):
        """
        Delete a project.

        Args:
            project_id (str): The ID of the project to delete.

        Returns:
            str: The status message indicating the success or failure of the project deletion.
        """
        url = f"{self.host}/api/projects/{project_id}/"
        response = requests.delete(url, headers=self._authorized_headers())
        if response.status_code == 204:
            return "Project deleted successfully."
        else:
            return "Error deleting project."

    @staticmethod
    def get_mime_type(file_name):
        extension = os.path.splitext(file_name)[1]
        return {
            '.json': 'application/json',
            '.csv': 'text/csv',
        }.get(extension, 'application/octet-stream')

    def upload_data(self, project_id, dataset_name, folder_path, file_names):
        url = f"{self.host}/api/projects/{project_id}/upload-data/"
        payload = {'dataset_folder_name': dataset_name}
        files = [
            ('files', (file_name, open(f'{folder_path}/{file_name}','rb'), self.get_mime_type(file_name))) for file_name in file_names
        ]
        headers = {
            'Authorization': f'Token {self.token}'
        }

        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        
        # Check if request was successful
        if response.status_code == 200:
            print('Files uploaded successfully.')
        else:
            print(f'Error occurred while uploading files: {response.text}')
        return response

    def upload_conf(self, project_id, file_path):
        url_upload_conf = f'{self.host}/api/projects/{project_id}/update-conf-file/'

        headers = {'Authorization': f'Token {self.token}'}
                #'Accept': 'application/json'}
        files=[
        ('file',('config.yaml',open(file_path,'rb'),'text/yaml'))
        ]
        response = requests.request("POST", url_upload_conf, headers=headers, files=files)
        print(response.text)

    def list_models(self):
        """This method lists all the available models"""
        url = f"{self.host_airflow}/api/v1/dags"
        response = self.session.get(url)
        if response.status_code == 200:
            models = response.json().get('dags', [])
            if models:
                print("Available Models:")
                table_data = []
                for item in models:
                    dag_id = item.get('dag_id')
                    description = item.get('description')
                    table_data.append([dag_id, description])

                headers = ['Model Name', 'Description']
                print(tabulate(table_data, headers=headers, tablefmt='pretty'))
            else:
                print("No models available.")
        else:
            print("Error fetching models.",response.status_code)

    def get_dag(self, dag_id):
        """This method returns the details of a specific dag"""
        url = f"{self.base_url}/api/v1/dags/{dag_id}"
        return self._api_get(url)

    def model_runs(self, dag_id):
        """This method returns the runs of a specific dag"""
        url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns"
        dag_runs = self._api_get(url)
        for dag_run in dag_runs["dag_runs"]:
            dag_run_id = dag_run["dag_run_id"]
            state = dag_run["state"]
            logging.info(f"Model run ID: {dag_run_id}, state: {state}")

    def synthetize(self):
        """This method triggers the synthetization process"""

        if not self.project_id or not self.dag_id:
            raise ValueError("Please specify project_id and dag_id.")

        now = datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")

        run_id = self.project_id + '_' + time

        url = f"{self.host_airflow}/api/v1/dags/{self.dag_id}/dagRuns"
        conf = {"main_data_dir": self.main_data_dir, "project_name": self.project_id}
        data = {"dag_run_id": run_id, "conf": conf}

        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            logging.info("Synthetization triggered successfully!")
            return 'Synthetization triggered successfully!'

        except requests.exceptions.HTTPError as errh:
            logging.error(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            logging.error(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            logging.error(f"Something went wrong: {err}")
        finally:
            self.project_id = None
            self.dag_id = None
