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
        
    def make_api_request(self, endpoint, method='GET', **request_args):
        try:
            url = f"{self.host_django}/{endpoint}"

            # Set default headers if not provided in request_args
            if 'headers' not in request_args:
                request_args['headers'] = {'Content-Type': 'application/json'}

            # Make the request based on the method
            if method.upper() == 'GET':
                response = requests.get(url, **request_args)
            elif method.upper() == 'POST':
                response = requests.post(url, **request_args)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, **request_args)

            response.raise_for_status()

            # Return None for empty response content (especially for DELETE requests)
            return response.json() if response.content else None

        except requests.HTTPError as e:
            logging.error(f"HTTP error occurred: {e.response.status_code} {e.response.reason} for URL {e.response.url}")
            raise
        except json.JSONDecodeError:
            # Handle empty response body
            if response.status_code in [204, 205]:
                return None
            else:
                raise
        except Exception as e:
            logging.error(f"Unexpected error during API request: {str(e)}")
            raise


    
    def __init__(self, host_django=None, host_airflow=None):
        """
        Initialize the syntheticus_client instance.

        Args:
            host_django (str, optional): The base URL of the Django API.
            host_airflow (str, optional): The base URL of the Airflow API.
        """
        self.host_django = host_django or os.getenv('DJANGO_URL')
        self.host_airflow = host_airflow or os.getenv('AIRFLOW_URL')

        if not self.host_django:
            raise ValueError("Host DJANGO_URL must be provided, either as environment variables or directly as arguments")
        
        self.token = os.getenv('USER_TOKEN')
        if not self.token:
            print("Warning: User token not found. Proceed with login after initialization.")
            
        self.user = None # username
        self.password = None # passwod
        
        self.projects_data = []
        self.table_data = []  # Initialize as an empty list
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
        self.commit_id = None # commit id
        
    # def register(self, username, email, password):
    #     """
    #     Register a new user.

    #     Args:
    #         username (str): The username for the new user.
    #         email (str): The email address for the new user.
    #         password (str): The password for the new user.

    #     Returns:
    #         dict: The response JSON containing the registration details, excluding the key.
    #     """
    #     url = f"{self.host}/dj-rest-auth/registration/"
    #     body = {
    #         "username": username,
    #         "email": email,
    #         "password1": password,
    #         "password2": password
    #     }
    #     try:
    #         response = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
    #         response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
            
    #         # If the response status is 200, parse the JSON response
    #         response_json = response.json()

    #         # If you want to remove the key from the response before returning
    #         if 'key' in response_json:
    #             del response_json['key']

    #         # If the response is empty, print a success message
    #         if not response_json:
    #             print("Successful registration!")

    #         return response_json

    #     except requests.exceptions.HTTPError as errh:
    #         # If a HTTPError is caught, print the response body for more information
    #         print(f"Http Error: {errh}. Response body: {errh.response.text}")
    #     except requests.exceptions.ConnectionError as errc:
    #         print(f"Error Connecting: {errc}. Response body: {errc.response.text}")
    #     except requests.exceptions.Timeout as errt:
    #         print(f"Timeout Error: {errt}. Response body: {errt.response.text}")
    #     except requests.exceptions.RequestException as err:
    #         print(f"An error occurred: {err}. Response body: {err.response.text}")
    #     except ValueError:
    #         print("Invalid response received. Unable to parse JSON.")

    def login(self, username, password):
        try:
            response = self.make_api_request(
                endpoint="dj-rest-auth/login/", 
                method='POST', 
                json={'username': username, 'password': password}  # Using 'json' to ensure proper JSON formatting
            )
            self.token = response.get('key')
            return "Login successful."
        except requests.HTTPError as e:
            return f"Login failed. HTTP error: {e.response.status_code} {e.response.reason}"
        except Exception as e:
            return f"Login failed. Error: {str(e)}"

    # def logout(self):
    #     """
    #     Log out from the API.

    #     Returns:
    #         str: The response text from the logout request.
    #     """
    #     url = f"{self.host_django}/dj-rest-auth/logout/"
    #     response = requests.post(url, headers=self._authorized_headers())
    #     return response.text

    # def change_password(self, new_password):
    #     """
    #     Change the user's password.

    #     Args:
    #         new_password (str): The new password.

    #     Returns:
    #         dict: The response JSON containing the password change details.
    #     """
    #     url = f"{self.host_django}/dj-rest-auth/password/change/"
    #     body = {
    #         "new_password1": new_password,
    #         "new_password2": new_password
    #     }
    #     response = requests.post(url, data=json.dumps(body), headers=self._authorized_headers())
    #     return response.json()

    # def get_user(self, user_id):
    #     """
    #     Get user details by user ID.

    #     Args:
    #         user_id (str): The ID of the user.

    #     Returns:
    #         str: The response text containing the user details.
    #     """
    #     url = f"{self.host_django}/api/users/{user_id}/"
    #     response = requests.get(url, headers=self._authorized_headers())
    #     return response.text

    # def get_me(self):
    #     """
    #     Get the current user's details.

    #     Returns:
    #         None
    #     """
    #     url = f"{self.host_django}/api/users/me/"
    #     response = requests.get(url, headers=self._authorized_headers())
    #     if response.status_code == 200:
    #         user_data = response.json()
    #         username = user_data.get('username')
    #         name = user_data.get('name')
    #         user_url = user_data.get('url')

    #         print("User details:")
    #         print(f"Username: {username}")
    #         print(f"Name: {name}")
    #         print(f"URL: {user_url}")
    #         print("-" * 20)
    #     else:
    #         print("Error fetching user details.")

    def get_projects(self):
        """
        Get the list of projects and update self.projects_data.
        """
        try:
            response = self.make_api_request(
                endpoint="api/projects/",
                method='GET',
                headers = self._authorized_headers()
            )
            
            self.projects_data = response.get('results', [])
            if not self.projects_data:
                print("No projects found.")
                return None

        except requests.HTTPError as e:
            error_message = f"Error fetching projects. HTTP error: {e.response.status_code} {e.response.reason}"
            logging.error(error_message)
            print(error_message)
            return None
        except Exception as e:
            error_message = f"Error fetching projects: {str(e)}"
            logging.error(error_message)
            print(error_message)
            return None
            
    def list_projects(self):
        self.get_projects()
        # Create a list of lists for each project row
        project_list = [[project.get('id'), project.get('name'), project.get('created_at')] 
                        for project in self.projects_data]

        # Use tabulate to format the table
        table = tabulate(project_list, headers=["Project ID", "Project Name", "Created At"], tablefmt="grid")

        # Print the formatted table
        print(table)
        return None
        
    def create_project(self, name):
        """
        Create a new project.

        Args:
            name (str): The name of the project.

        Raises:
            Exception: If the project creation fails.
        """
        try:
            response = self.make_api_request(
                endpoint="api/projects/",
                method='POST',
                data=json.dumps({'name': name}),
                headers = self._authorized_headers()
            )

            project_data = response
            project_id = project_data.get('id')
            self.projects[project_id] = project_data.get('name')
            self.project_id = project_id

            # Format and print the success message
            success_message = (
                f"Project '{name}' created and selected successfully.\n"
                f"Project ID: {project_id}\n"
                f"Project Name: {project_data.get('name')}\n"
                f"Created At: {project_data.get('created_at')}"
            )
            print(success_message)

            # Optionally, return the raw project data without the message
            #return project_data

        except requests.HTTPError as e:
            error_message = f"Error creating the project. HTTP error: {e.response.status_code} {e.response.reason}"
            logging.error(error_message)
            raise Exception(error_message)
        except Exception as e:
            error_message = f"Error creating the project: {str(e)}"
            logging.error(error_message)
            raise Exception(error_message)
    
    def select_project(self, project_id):

        if not self.projects_data:
            self.get_projects()
            
        project = next((proj for proj in self.projects_data if proj.get('id') == project_id), None)

        if project:
            self.project_id = project_id
            self.project_name = project.get('name')
            print(f"Project selected: {project_id} with name {self.project_name}")
        else:
            print(f"Project with ID {project_id} not found.")
            
    def delete_project(self, project_id):
        """
        Delete a project.

        Args:
            project_id (str): The ID of the project to delete.

        Returns:
            str: The status message indicating the success or failure of the project deletion.

        Raises:
            Exception: If the project deletion fails.
        """
        try:
            self.make_api_request(
                endpoint=f"api/projects/{project_id}/",
                method='DELETE',
                headers = self._authorized_headers()
            )
            print("Project deleted successfully.")

        except requests.HTTPError as e:
            error_message = f"Error deleting project. HTTP error: {e.response.status_code} {e.response.reason}"
            logging.error(error_message)
            raise Exception(error_message)

        except Exception as e:
            error_message = f"Error deleting project: {str(e)}"
            logging.error(error_message)
            raise Exception(error_message)
    
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
        
        # Check if the current project_id exists in projects_data
        if not any(proj for proj in self.projects_data if proj['id'] == self.project_id):
            print("Please select a valid project ID.")
            return
        
        # Prepare the endpoint URL
        endpoint = f"api/projects/{self.project_id}/list-dataset-folders/"
        payload = {}
        files = {}
        headers = {
        'Authorization': f'Token {self.token}'
        }
        # Use make_api_call to perform the API request
        self.data = self.make_api_request(endpoint=endpoint, method="GET", headers=headers, data=payload, files=files)

        #self.data = response.get('results', [])
        return None
    
    def list_datasets(self):
        self.get_datasets()
        # Prepare data for table
        self.table_data = []
        for result in self.data.get('results', []):
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
                    self.table_data.append(row)

                    # Add the dataset to the lookup dictionary using its unique ID as the key
                    self.datasets[result.get('id')] = dataset.get('dataset_name')

        # Define table headers
        headers = ['Dataset Name', 'Dataset ID', 'Project ID', 'Data Type', 'Size', 'Number of Rows', 'Number of Columns', 'Status']

        # Print table
        print(tabulate(self.table_data, headers=headers, tablefmt='pretty'))
        return None

    def select_dataset(self, dataset_id):
        if dataset_id in self.datasets:
            self.dataset_id = dataset_id
            self.dataset_name  = self.datasets[dataset_id]  
            print(f"Dataset selected: {dataset_id} with name {self.datasets[dataset_id]}")
        else:
            print(f"Dataset with ID {dataset_id} not found.")

    @staticmethod
    def get_mime_type(file_name):
        extension = os.path.splitext(file_name)[1]
        return {
            '.json': 'application/json',
            '.csv': 'text/csv',
        }.get(extension, 'application/octet-stream')

    def upload_data(self, dataset_name, folder_path, file_names):
        # Check if the current project_id exists in projects_data
        if not any(proj for proj in self.projects_data if proj['id'] == self.project_id):
            print("Please select a valid project ID.")
            return

        url = f"{self.host_django}/api/projects/{self.project_id}/upload-data/"
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
            print(f'Error occurred while uploading files: STATUS CODE {response.status_code}')
        return

    def upload_conf(self):
        url_upload_conf = f'{self.host_django}/api/projects/{self.project_id}/update-conf-file/'

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
            print(f"Error occurred while uploading the configuration file: STATUS CODE {response.status_code}")
            
    def update_conf(self):
        url_upload_conf = f'{self.host_django}/api/projects/{self.project_id}/update-conf-file/'

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
            print(f"Error occurred while re-uploading the configuration file: STATUS CODE {response.status_code}")

    def get_models(self):
        """Fetches the available models and stores them in self.models."""
        url = f"{self.host_airflow}/api/v1/dags"
        response = self.session.get(url)
        if response.status_code == 200:
            self.models = response.json().get('dags', [])
        else:
            print(f"Error fetching models. Status Code: {response.status_code}")
            self.models = []

 
    def list_models(self):
        self.get_models()
        """Prints the available models, if any."""
        if self.models:
            print("Available Models:")
            table_data = []
            for item in self.models:
                dag_id = item.get('dag_id')
                description = item.get('description')
                table_data.append([dag_id, description])

            headers = ['Model ID', 'Description']
            print(tabulate(table_data, headers=headers, tablefmt='pretty'))
        else:
            print("No models available.")

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

    # def fit(self):
    #     """
    #     Triggers the fit process for the selected model.

    #     Raises:
    #         Exception: If an unexpected error occurs during the fit process.

    #     Returns:
    #         str: A message indicating the success or failure of the fit process.

    #     """
    #     url = f"{self.host_django}/api/projects/{self.project_id}/run-dag/"

    #     payload = json.dumps({
    #         "dag_name": f"{self.model_id}",
    #     })
    #     headers = {
    #         'Content-Type': 'application/json',
    #         'Authorization': f'Token {self.token}'
    #     }

    #     try:
    #         response = requests.request("POST", url, headers=headers, data=payload)
    #         response.raise_for_status()

    #         # Join the response strings into one string
    #         response_string = ''.join(json.loads(response.text))

    #         # Convert the JSON string into a dictionary
    #         response_dict = json.loads(response_string)

    #         # Print the important information in a nice way
    #         print(f"Project Name: {response_dict['conf']['project_name']}")
    #         print(f"Model name: {response_dict['dag_id']}")
    #         print(f"Model Run ID: {response_dict['dag_run_id']}")
    #         print(f"Execution Date: {response_dict['execution_date']}")
    #         print(f"State: {response_dict['state']}")
    #         print('')
    #         print('The fit process has been triggered successfully.')
    #         return 'The fit process has been triggered successfully.'

    #     except requests.exceptions.RequestException as err:
    #         logging.error(f"An error occurred during the fit process: {err}")
    #         return "An error occurred during the fit process."
    
    #### the following will be deprecated in future versions. Use django API instead.    
    def synthetize(self):
        """
        Triggers the data synthesis process.

        Raises:
            ValueError: If project_id or model_id is not specified.
            Exception: For any other unexpected errors.

        Returns:
            str: Success message if synthesis is triggered successfully.
            str: Error message if synthesis trigger encounters an error.

        """
        try:
            if not self.project_id or not self.model_id:
                raise ValueError("Please specify project_id and model_id.")

            now = datetime.now()
            time = now.strftime("%Y-%m-%d %H:%M:%S")
            run_id = self.project_id + '_' + time

            url = f"{self.host_airflow}/api/v1/dags/{self.model_id}/dagRuns"
            conf = {"main_data_dir": self.main_data_dir, "project_name": self.project_id}
            data = {"dag_run_id": run_id, "conf": conf}

            # Print information before triggering synthesis
            print(f"Synthesis Information:")
            print(f"Project: {self.project_name} (ID: {self.project_id})")
            print(f"Dataset: {self.dataset_name} (ID: {self.dataset_id})")
            print(f"Model: {self.model_id}")
            print(f"Configuration File: {self.config_file_path}")

            response = self.session.post(url, json=data)
            response.raise_for_status()

            if response.status_code // 100 == 2:  # Check if status code is in the 2xx range
                logging.info("Synthesis triggered successfully!")
                return 'Synthesis triggered successfully!'
            else:
                logging.error(f"Synthesis trigger returned HTTP {response.status_code}: {response.text}")
                return f"Synthesis trigger failed with HTTP {response.status_code}."

        except requests.exceptions.RequestException as err:
            logging.error(f"An error occurred during synthesis: {err}")
            return "An error occurred during synthesis."
        
    def get_commits(self):
        """
        Fetches commits for the selected project and stores them in self.commits.
        """
        if self.project_id is None:
            print('Please select a project_id first.')
            self.commits = None
            return

        endpoint = f"api/projects/{self.project_id}/commit-logs/"
        headers = {'Authorization': f'Token {self.token}'}

        try:
            # make_api_request might return a JSON-decoded response or None
            commits_data = self.make_api_request(endpoint=endpoint, method="GET", headers=headers)

            if commits_data is None:
                # This could mean no data found or a successful operation with no content (204 No Content)
                print("No commits data found or received an empty response.")
                self.commits = None
            else:
                # Successfully retrieved data
                self.commits = commits_data

        except requests.HTTPError as http_err:
            # Handle HTTP errors separately
            print(f"HTTP error occurred: {http_err}")
            self.commits = None
        except Exception as e:
            # Handle any other exceptions
            print(f"An error occurred while making the API request: {e}")
            self.commits = None

    def list_commits(self):
        """
        Prints the fetched commits for the selected project.

        Returns:
            None
        """
        self.get_commits()
        if not self.commits:
            print("No commits available or commits have not been fetched yet.")
            return

        print(f'List of commits in the selected project ({self.project_id}):')
        print(tabulate(self.commits, headers="keys", tablefmt="pretty"))


    def select_commit(self, commit_id):
        """
        Selects a commit for the current project.

        Args:
            commit_id (str): The ID of the commit to select.

        Returns:
            None

        """
        if self.project_id is not None:
            self.commit_id = commit_id
            print(f"Commit {commit_id} selected in project {self.project_id}.")
        else:
            print("Please select a project_id first using the select_project() method.")

    def download_data(self, data_to_download):
        """
        Downloads data from a specified source based on the given parameters.

        Args:
            data_to_download (str): The type of data to download. Options are 'data_synth', 'models', 'report', 'config', 'metadata'.

        Returns:
            None

        Raises:
            ConnectionError: If there's an issue with the HTTP request.
            JSONDecodeError: If the response from the server is not a valid JSON format.
            IOError: If there are issues with file operations.
            ValueError: If the parameter values are incorrect or unexpected.
            Exception: For any other unexpected errors.

        """
        try:
            if self.project_id and self.commit_id is not None:
                # Construct the URL for the API endpoint
                url = f"{self.host_django}/api/projects/{self.project_id}/download-airflow-data/"
                
                # Prepare payload for the POST request
                payload = json.dumps({
                    "commit": f"{self.commit_id}",
                    "data_to_download": f"{data_to_download}"
                })
                
                # Define headers for the POST request
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {self.token}'
                }

                # Make the POST request
                response = requests.request("POST", url, headers=headers, data=payload)
                
                # Process different types of downloaded data
                if data_to_download == 'data_synth' or data_to_download == 'data_real':
                    # Save the response content to a zip file
                    with open(f"{self.dataset_name}_synth.zip", 'wb') as f:
                        f.write(response.content)
                        
                    # Extract and process files from the downloaded zip
                    with zipfile.ZipFile(io.BytesIO(response.content), 'r') as z:
                        for filename in z.namelist():
                            if filename.endswith('.pkl'):
                                # Load the DataFrame from the pickled data
                                df = pd.read_pickle(z.open(filename))
                                # Save the DataFrame to a csv file
                                df.to_csv(f"{self.dataset_name}_synth.csv", index=False)
                elif data_to_download == 'report':
                    with open(f"{self.project_name}_reports.pdf", 'wb') as f:
                        f.write(response.content)
            else:
                print("Please select a project_id and a commit first.")
        except (ConnectionError, requests.RequestException) as e:
            print(f"An error occurred while making the request: {e}")
        except json.JSONDecodeError as e:
            print(f"An error occurred while decoding the JSON response: {e}")
        except IOError as e:
            print(f"An error occurred during file operations: {e}")
        except ValueError as e:
            print(f"An error occurred due to invalid parameter values: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def reset(self):
        """Resets all specified instance variables to None."""
        self.projects_data = []
        self.table_data = []  # Initialize as an empty list
        self.projects = {} # dictionary with the list of projects
        self.datasets = {} # dictionary with the list of datasets for a project
        
        self.project_id = None
        self.project_name = None
        self.model_id = None
        self.dataset_id = None
        self.dataset_name = None
        self.config_file_path = None
        self.commit_id = None
        
    def show_setup(self):
            """Prints the current setup information in a readable format."""
            print("Current Setup Information:")
            print(f"Project ID: {self.project_id or 'Not Set'}")
            print(f"Project Name: {self.project_name or 'Not Set'}")
            print(f"Dataset ID: {self.dataset_id or 'Not Set'}")
            print(f"Model ID: {self.model_id or 'Not Set'}")
            print(f"Dataset Name: {self.dataset_name or 'Not Set'}")
            print(f"Config File Path: {self.config_file_path or 'Not Set'}")
            print(f"Commit ID: {self.commit_id or 'Not Set'}")