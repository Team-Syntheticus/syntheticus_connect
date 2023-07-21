import requests
import json
import logging
import os
from datetime import datetime
from tabulate import tabulate
import os
from IPython.core.getipython import get_ipython
import yaml
from ruamel.yaml import YAML
import os
import textwrap
import pandas as pd
import zipfile
import io

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

        self.host = host + ':8000' # host syntheticus nav
        self.host_airflow = host + ':8080' # host airflow
        self.token = None # user token assigned at login
        self.user = None # username
        self.password = None # passwod
        self.projects = {} # dictionary with the list of projects
        self.datasets = {} # dictionary with the list of datasets for a project
        self.session = requests.Session()
        self.session.auth = ('airflow', 'airflow') # airflow credentials will be deprecated
        self.main_data_dir = './media/' # directory in syntheticus nav
        self.project_id = None # selected project id
        self.project_name = None # selected project name
        self.model_id = None  # selected model id
        self.dataset_id = None # selected dataset id
        self.dataset_name = None # selected dataset name
        self.config_file_path = None # path to the config file
        self.commit = None # commit id
        
    def register(self, username, email, password):
        """
        Register a new user.

        Args:
            username (str): The username for the new user.
            email (str): The email address for the new user.
            password (str): The password for the new user.

        Returns:
            dict: The response JSON containing the registration details, excluding the key.
        """
        url = f"{self.host}/dj-rest-auth/registration/"
        body = {
            "username": username,
            "email": email,
            "password1": password,
            "password2": password
        }
        try:
            response = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
            
            # If the response status is 200, parse the JSON response
            response_json = response.json()

            # If you want to remove the key from the response before returning
            if 'key' in response_json:
                del response_json['key']

            # If the response is empty, print a success message
            if not response_json:
                print("Successful registration!")

            return response_json

        except requests.exceptions.HTTPError as errh:
            # If a HTTPError is caught, print the response body for more information
            print(f"Http Error: {errh}. Response body: {errh.response.text}")
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}. Response body: {errc.response.text}")
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}. Response body: {errt.response.text}")
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}. Response body: {err.response.text}")
        except ValueError:
            print("Invalid response received. Unable to parse JSON.")



    def login(self, username, password):
        """
        Log in to the API.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.

        Returns:
            str: The login status message.
        """
        
        # reinitailzias variables
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
            self.project_id = project_id    
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
                        "Selected" if project.get('id') == self.project_id else "Not Selected"
                    ]
                    table_data.append(row)
                    # Update the project lookup dictionary
                    self.projects[project.get('id')] = project.get('name')

                # Define table headers
                headers = ['Project ID', 'Project Name', 'Created At', 'Status']

                # Print table
                print("Projects:")
                print(tabulate(table_data, headers=headers, tablefmt='pretty'))
            else:
                print("No projects found.")
        else:
            print("Error fetching projects.")
    
    def select_project(self, project_id):
        if project_id in self.projects:
            self.project_id = project_id
            self.project_name = self.projects[project_id]
            print(f"Project selected: {project_id} with name {self.projects[project_id]}")
        else:
            print(f"Project with ID {project_id} not found.")
    
    def wrap_text(text, width):
        wrapped_lines = textwrap.wrap(text, width=width)
        wrapped_text = '\n'.join(wrapped_lines)
        return wrapped_text
    
    def get_datasets(self):
        """
        List the dataset folders for a project.

        Args:
            project_id (str): The ID of the project.

        Returns:
            dict: The response JSON containing the dataset folders.
        """
        
        # Check if project_id exists in the lookup dictionary
        if self.project_id not in self.projects:
            print("Please select a valid project ID.")
            return
        url = f"{self.host}/api/projects/{self.project_id}/list-dataset-folders/"
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
                        result.get('id'),
                        result.get('project'),
                        result.get('data_type'),
                        dataset.get('size'),
                        dataset.get('rows_number'),
                        len(dataset.get('dataset_metadata', {}).get('column_types', {})),
                        'Selected' if self.dataset_id == result.get('id') else 'Not Selected',
                    ]
                    table_data.append(row)

                    # Add the dataset to the lookup dictionary using its unique ID as the key
                    self.datasets[result.get('id')] = dataset.get('dataset_name')

        # Define table headers
        headers = ['Dataset Name', 'Dataset ID', 'Project ID', 'Data Type', 'Size', 'Number of Rows', 'Number of Columns', 'Status']

        # Print table
        print(tabulate(table_data, headers=headers, tablefmt='pretty'))

    def select_dataset(self, dataset_id):
        if dataset_id in self.datasets:
            self.dataset_id = dataset_id
            self.dataset_name  = self.datasets[dataset_id]  
            print(f"Dataset selected: {dataset_id} with name {self.datasets[dataset_id]}")
        else:
            print(f"Dataset with ID {dataset_id} not found.")

        
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

    def upload_data(self, dataset_name, folder_path, file_names):
        # Check if project_id exists in the lookup dictionary
        if self.project_id not in self.projects:
            print("Please select a valid project ID.")
            return

        url = f"{self.host}/api/projects/{self.project_id}/upload-data/"
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
        return

    def upload_conf(self):
        url_upload_conf = f'{self.host}/api/projects/{self.project_id}/update-conf-file/'

        # Prepare the configuration data
        config_data = {
            'config_version': '1.0',
            'config_name': 'base',
            'config_steps': [
                {
                    'data': {
                        'dataset_version': self.dataset_id,  # Use the selected project ID
                    },
                },
                {'transform': None},
                {'model': None},
                {
                    'sample': {
                        'number_of_rows': '',
                    },
                },
                {'metrics': None},
            ]
        }

        # Save configuration data to a YAML file with the same name as the project
        self.config_file_path = f"{self.project_name}.yaml"
        yaml = YAML()
        with open(self.config_file_path, 'w') as file:
            yaml.dump(config_data, file)

        headers = {'Authorization': f'Token {self.token}'}
        files = [('file', (self.config_file_path, open(self.config_file_path, 'rb'), 'text/yaml'))]
        response = requests.request("POST", url_upload_conf, headers=headers, files=files)

        if response.status_code == 200:
            print(f"A basic configuration file has been uploaded in the project {self.project_id}.")
            print(f"If you want to modify the config file, open the file with {self.project_name}.yaml and customize it.")
            print("Once finished, save and upload again using the update_conf() method.")
        else:
            print(f"Error occurred while uploading the configuration file: {response.text}")
            
    def update_conf(self):
        url_upload_conf = f'{self.host}/api/projects/{self.project_id}/update-conf-file/'

        # Check if the configuration file exists
        self.config_file_path = f"{self.project_name}.yaml"
        if not os.path.isfile(self.config_file_path):
            print("Configuration file not found.")
            return

        # Upload the configuration file
        headers = {'Authorization': f'Token {self.token}'}
        files = [('file', (self.config_file_path, open(self.config_file_path, 'rb'), 'text/yaml'))]
        response = requests.request("POST", url_upload_conf, headers=headers, files=files)

        if response.status_code == 200:
            print(f"The configuration file '{self.config_file_path}' has been successfully re-uploaded.")
        else:
            print(f"Error occurred while re-uploading the configuration file: {response.text}")

    def get_models(self):
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

                headers = ['Model ID', 'Description']
                print(tabulate(table_data, headers=headers, tablefmt='pretty'))
            else:
                print("No models available.")
        else:
            print("Error fetching models.",response.status_code)

    def select_model(self, model_id):
            self.model_id = model_id
            print(f"Model {model_id} selected.")
    
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

    def fit(self):
        url = f"{self.host}/api/projects/{self.project_id}/run-dag/"

        payload = json.dumps({
        "dag_name": f"{self.model_id}",
        })
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {self.token}'
        }

        try:
            response = requests.request("POST", url, headers=headers, data=payload)

            # Join the response strings into one string
            response_string = ''.join(json.loads(response.text))

            # Convert the JSON string into a dictionary
            response_dict = json.loads(response_string)

            # Print the important information in a nice way
            print(f"Project Name: {response_dict['conf']['project_name']}")
            print(f"Model name: {response_dict['dag_id']}")
            print(f"Model Run ID: {response_dict['dag_run_id']}")
            print(f"Execution Date: {response_dict['execution_date']}")
            print(f"State: {response_dict['state']}")
            print('')
            print('The synthetization process has been triggered successfully.')
            
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
            self.dataset_id = None
            self.model_id = None
            self.sconfig_file_path = None

        
     
    #### the following will be deprecated in future versions. Use django API instead.    
    def synthetize(self):
        """This method triggers the synthetization process"""

        if not self.project_id or not self.model_id:
            raise ValueError("Please specify project_id and model_id.")

        now = datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")

        run_id = self.project_id + '_' + time

        url = f"{self.host_airflow}/api/v1/dags/{self.model_id}/dagRuns"
        conf = {"main_data_dir": self.main_data_dir, "project_name": self.project_id}
        data = {"dag_run_id": run_id, "conf": conf}

        try:
            # Print information before triggering synthetization
            print(f"Synthetization Information:")
            print(f"Project: {self.project_name} (ID: {self.project_id})")
            print(f"Dataset: {self.dataset_name} (ID: {self.dataset_id})")
            print(f"Model: {self.model_id}")
            print(f"Configuration File: {self.config_file_path}")

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
            self.dataset_id = None
            self.model_id = None
            self.sconfig_file_path = None

    def list_commits(self):
        url = f"{self.host}/api/projects/{self.project_id}/commit-logs/"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status() 

        commits = response.json()
        print(f'List of experiment in the project selected: {self.project_id}.')
        print(tabulate(commits, headers="keys", tablefmt="pretty"))
        
    def select_commit(self, commit_id):
            if self.project_id is not None:
                self.commit = commit_id
                print(f"Commit {commit_id} selected in project {self.project_id}.")
            else: 
                print("Please select a project_id first.")
                
    # def download_data(self, data_to_download):
    #     if self.project_id and self.commit is not None:
    #         url = f"{self.host}/api/projects/{self.project_id}/download-airflow-data/"
    #         payload = json.dumps({
    #         "commit": f"{self.commit}",
    #         "data_to_download": f"{data_to_download}"
    #         })
    #         headers = {
    #         'Content-Type': 'application/json',
    #         'Authorization': f'Token {self.token}'
    #         }

    #         response = requests.request("POST", url, headers=headers, data=payload)

    #         # # Load the pickled DataFrame from the response
    #         # df = pickle.loads(response.content)

    #         # # Define the filename
    #         # filename = f"{self.dataset_name}_synth.csv"

    #         # # Save DataFrame to CSV file
    #         # df.to_csv(filename, index=False)
    #                 # Save the response content to a file
    #         #with open('response.pkl', 'wb') as f:
    #         #    f.write(response.content)

    #     else:
    #         print("Please select a project_id and a commit first.")

    def download_data(self, data_to_download):
        if self.project_id and self.commit is not None:
            url = f"{self.host}/api/projects/{self.project_id}/download-airflow-data/"
            payload = json.dumps({
                "commit": f"{self.commit}",
                "data_to_download": f"{data_to_download}"
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Token {self.token}'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            # Save the response content to a zip file
            with open(f"{self.dataset_name}_synth.zip", 'wb') as f:
                f.write(response.content)
                
            # Open the zip file
            with zipfile.ZipFile(io.BytesIO(response.content), 'r') as z:
                # Loop through each file
                for filename in z.namelist():
                    # If the file is a .pkl file
                    if filename.endswith('.pkl'):
                        # Load the DataFrame from the pickled data
                        df = pd.read_pickle(z.open(filename))
                        # Save the DataFrame to a csv file
                        df.to_csv(f"{self.dataset_name}_synth.csv", index=False)

        else:
            print("Please select a project_id and a commit first.")
