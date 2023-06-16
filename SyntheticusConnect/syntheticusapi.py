import requests
import json
import os
import logging

class SyntheticusConnect:
    
    def __init__(self, base_url, username, password, main_data_dir='/opt/airflow/data/'):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.main_data_dir = main_data_dir
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        
    def _api_get(self, url):
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.error(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            logging.error(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            logging.error(f"Something went wrong: {err}")
        return json.loads(response.text)

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

    def synthetize(self, dag_id, run_id=None, project_name=None):
        """This method triggers the synthetization process"""
        url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns"
        conf = {"main_data_dir": self.main_data_dir, "project_name": project_name}
        data = {"dag_run_id": run_id, "conf": conf}
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            logging.info("Synthetization triggered successfully!")
        except requests.exceptions.HTTPError as errh:
            logging.error(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            logging.error(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            logging.error(f"Something went wrong: {err}")

    def list_models(self):
        """This method lists all the available models"""
        url = f"{self.base_url}/api/v1/dags"
        models = self._api_get(url)
        for item in models['dags']:
           logging.info(f"Model name: {item['dag_id']}, description: {item['description']}")

    def simple_visualize(self,project_name):
        """This method visualizes the synthetized data"""
        os.chdir('/data')
        folder_path = f"{project_name}/airflow_data/data_synth"
        try:
            for filename in os.listdir(folder_path):
                if filename.endswith(".pkl"):
                    file_path = os.path.join(folder_path, filename)
                    df = pd.read_pickle(file_path)
                    logging.info(f"Table from {filename}:")
                    logging.info(df)
        except FileNotFoundError:
            logging.error("File not found")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

