from ipywidgets import widgets, Layout, Button, Text, Password, VBox, Output, Dropdown
from IPython.display import display

from syntheticus_connect import syntheticus_client
from contextlib import contextmanager
import yaml
import requests

class syntheticus_interact(syntheticus_client):
    def __init__(self, host_django=None, host_airflow=None):
        super().__init__(host_django, host_airflow)
    
    # @contextmanager
    # def suppress_output(self):
    #     with Output():
    #         yield
    
    def login_user(self):
        username_input = Text(placeholder='Username')
        password_input = Password(placeholder='Password')
        login_button = Button(description='Login')
        output_area = Output()

        def on_login_button_click(b):
            self.user = str(username_input.value)
            self.password = str(password_input.value)
            # Call the login method of syntheticus_client and display the response
            with output_area:
                response = self.login(self.user, self.password)
                print(response)  # This will output to the output_area widget

        login_button.on_click(on_login_button_click)

        display(VBox([username_input, password_input, login_button, output_area]))

    def project_select(self):
        """
        Create a project selection dropdown widget.
        """
        # Fetch project data
        self.get_projects()

        # Remove duplicate projects if any (based on project ID)
        unique_projects = {proj['id']: proj for proj in self.projects_data}.values()

        # Prepare project strings for the dropdown
        project_strings = [f"ID: {project['id']}, Name: {project['name']}"
                           for project in unique_projects] or ["No projects available"]

        # Create or update the Dropdown widget
        if hasattr(self, 'project_dropdown_widget'):
            self.project_dropdown_widget.options = project_strings
            self.project_dropdown_widget.value = project_strings[0] if project_strings else None
        else:
            self.project_dropdown_widget = Dropdown(
                options=project_strings,
                value=project_strings[0] if project_strings else None,
                description='Select:',
                disabled=not bool(project_strings),
                layout=Layout(width='auto')
            )

        # Create or update the Output area
        if not hasattr(self, 'project_output_area'):
            self.project_output_area = Output()

        def update_variables(change):
            """
            Update variables based on the selected dropdown value.

            This function is called whenever the dropdown value changes.
            It updates the selected project's information and displays it.

            Args:
                change (dict): A dictionary containing information about the change.

            Returns:
                None
            """
            selected_value = change['new']

            # Extract the project ID from the selected dropdown value
            selected_project_id = selected_value.split(",")[0].split(":")[1].strip()

            # Find the corresponding project in the projects_data
            selected_project = next((proj for proj in self.projects_data if str(proj['id']) == selected_project_id), None)

            if selected_project:
                self.project_id = selected_project['id']
                self.project_name = selected_project['name']

                # Clear previous output and display the new project info
                with self.project_output_area:
                    self.project_output_area.clear_output()
                    print(f"Selected Project ID: {self.project_id}")
                    print(f"Selected Project Name: {self.project_name}")

        # Attach the update function to the dropdown's 'value' property changes
        self.project_dropdown_widget.observe(update_variables, names='value')

        # Check if there's only one project in the dropdown
        if len(project_strings) == 1:
            update_variables({'new': self.project_dropdown_widget.value})

        # Display the Dropdown widget and the output area
        display(VBox([self.project_dropdown_widget, self.project_output_area]))

    def dataset_select(self):
        self.get_datasets()

        # Group datasets by ID and count the number of files/tables per ID
        datasets_by_id = {}
        for result in self.data.get('results', []):
            for outer_dataset in result.get('datasets', []):
                for dataset in outer_dataset.get('datasets', []):
                    dataset_id = result.get('id')
                    if dataset_id not in datasets_by_id:
                        datasets_by_id[dataset_id] = {
                            'count': 0,
                            'name': dataset.get('dataset_name'),
                            'project_id': result.get('project'),
                            'data_type': result.get('data_type'),
                            'size': dataset.get('size'),
                            'rows_number': dataset.get('rows_number'),
                            'num_columns': len(dataset.get('dataset_metadata', {}).get('column_types', {})),
                            'status': 'Selected' if self.dataset_id == dataset_id else 'Not Selected'
                        }
                    datasets_by_id[dataset_id]['count'] += 1

        # Prepare dataset strings for the dropdown
        dataset_strings = [f"ID: {dataset_id}, Name: {info['name']} (# of tables: {info['count']})"
                           for dataset_id, info in datasets_by_id.items()]
        dataset_strings.insert(0, "Select a dataset")

        self.dataset_dropdown_widget = widgets.Dropdown(
            options=dataset_strings,
            value=dataset_strings[0],
            description='Select:',
            disabled=False,
            layout=Layout(width='auto')
        )

        self.dataset_output_area = Output()

        def update_variables(change):
            selected_value = change['new']
            selected_index = dataset_strings.index(selected_value) - 1  # Adjust for 'Select a dataset'

            if selected_index >= 0:
                selected_dataset_id = list(datasets_by_id.keys())[selected_index]
                selected_dataset_info = datasets_by_id[selected_dataset_id]

                self.dataset_id = selected_dataset_id
                self.dataset_name = selected_dataset_info['name']

                with self.dataset_output_area:
                    self.dataset_output_area.clear_output()
                    print(f"Selected dataset ID: {self.dataset_id}")
                    print(f"Selected dataset Name: {self.dataset_name}")
                    print(f"Project ID: {selected_dataset_info['project_id']}")
                    print(f"Data Type: {selected_dataset_info['data_type']}")
                    print(f"Size: {selected_dataset_info['size']}")
                    print(f"Number of Rows: {selected_dataset_info['rows_number']}")
                    print(f"Number of Columns: {selected_dataset_info['num_columns']}")
                    print("\n")
            else:
                with self.dataset_output_area:
                    self.dataset_output_area.clear_output()

        self.dataset_dropdown_widget.observe(update_variables, names='value')

        display(VBox([self.dataset_dropdown_widget, self.dataset_output_area]))

    def create_config_file(self):
        # Widget definitions
        transform_table_name_widget = widgets.Text(description='Table Name:', value='')
        transform_type_widget = widgets.Dropdown(
            description='Type:',
            options=['drop', 'fake', 'hash', 'number_shift', 'date_shift', 'generalize', 'shuffle', 'k_anonymity', 'l_diversity', 't_closeness', 'perturbation', 'tokenization'],
            value='drop')
        transform_columns_widget = widgets.Textarea(description='Columns:', value='')

        model_type_widget = widgets.Text(description='Model Type:', value='')

        sample_number_rows_widget = widgets.IntText(description='Number of Rows:', value=100)

        metrics_table_name_widget = widgets.Text(description='Table Name:', value='')
        metrics_column_plot_widget = widgets.Textarea(description='Column Plot:', value='')

        # Organize widgets into sections
        transform_section_widgets = VBox([transform_table_name_widget, transform_type_widget, transform_columns_widget])
        model_section_widgets = VBox([model_type_widget])
        sample_section_widgets = VBox([sample_number_rows_widget])
        metrics_section_widgets = VBox([metrics_table_name_widget, metrics_column_plot_widget])

        # Accordion to hold sections
        accordion = widgets.Accordion(children=[transform_section_widgets, model_section_widgets, sample_section_widgets, metrics_section_widgets])
        accordion.set_title(0, 'Transform')
        accordion.set_title(1, 'Model')
        accordion.set_title(2, 'Sample')
        accordion.set_title(3, 'Metrics')

        # Function to Generate Configuration
        def generate_config():
            config_yaml_lines = [
                "config_version: '1.0'",
                "config_name: base",
                "config_steps:"
            ]

            # Add 'data' section
            config_yaml_lines.append("  - data:")
            config_yaml_lines.append(f"      dataset_version: {self.dataset_id}")

            # Add 'transform' section
            if transform_table_name_widget.value or transform_columns_widget.value:
                # Assuming some logic to format transform section
                pass
            else:
                config_yaml_lines.append("  - transform:")

            # Add 'model' section
            if model_type_widget.value:
                # Assuming some logic to format model section
                pass
            else:
                config_yaml_lines.append("  - model:")

            # Add 'sample' section
            if sample_number_rows_widget.value:
                config_yaml_lines.append("  - sample:")
                config_yaml_lines.append(f"      number_of_rows: {sample_number_rows_widget.value}")
            else:
                config_yaml_lines.append("  - sample:")

            # Add 'metrics' section
            if metrics_table_name_widget.value or metrics_column_plot_widget.value:
                # Assuming some logic to format metrics section
                pass
            else:
                config_yaml_lines.append("  - metrics:")

            return "\n".join(config_yaml_lines)

        # Function to Handle Submit Action
        def on_submit_clicked(b):
            config_yaml = generate_config()

            # Save the generated configuration to a file
            self.config_file_path = f"{self.project_name}.yaml"
            with open(self.config_file_path, 'w') as file:
                file.write(config_yaml)
            
            # Now call upload_conf to upload the file
            self.upload_gen_conf()

        submit_button = Button(description="Create Config")
        submit_button.on_click(on_submit_clicked)

        # Display the Widget
        display(accordion, submit_button)

    def upload_gen_conf(self):
        url_upload_conf = f'{self.host_django}/api/projects/{self.project_id}/update-conf-file/'

        # Read the saved YAML file and upload it
        with open(self.config_file_path, 'rb') as file:
            files = [('file', (self.config_file_path, file, 'text/yaml'))]
            headers = {'Authorization': f'Token {self.token}'}
            response = requests.request("POST", url_upload_conf, headers=headers, files=files)

        if response.status_code == 200:
            print(f"A configuration file has been uploaded for the project {self.project_id}.")
        else:
            print(f"Error occurred while uploading the configuration file: STATUS CODE {response.status_code}")
    
    def model_select(self):

        self.get_models()

        models_data = []
        for model in self.models:
            models_data.append({
                'id': model['dag_id'],
                'description': model['description']
            })

        model_strings = [f"Name: {entry['id']}, description: {entry['description']}" for entry in models_data]
        model_strings.insert(0, "Select a model")

        self.model_dropdown_widget = widgets.Dropdown(
            options=model_strings,
            value=model_strings[0],
            description='Select:',
            disabled=False,
            layout=Layout(width='auto')
        )

        self.model_output_area = Output()

        def update_variables(change):
            selected_value = change['new']
            selected_index = model_strings.index(selected_value)
            selected_index = selected_index - 1

            if selected_index >= 0:
                selected_model = models_data[selected_index]
                self.model_id = selected_model['id']

                with self.model_output_area:
                    self.model_output_area.clear_output()
                    print(f"Selected model ID: {self.model_id}")
                    print(f"Selected model description: {selected_model['description']}")
            else:
                with self.model_output_area:
                    self.model_output_area.clear_output()

        self.model_dropdown_widget.observe(update_variables, names='value')

        display(VBox([self.model_dropdown_widget, self.model_output_area]))
        
    def experiment_select(self):
        """
        Displays a dropdown widget for commit selection.

        Returns:
            None
        """
        self.get_commits()  # Fetch commits data
        if not self.commits:
            print("No commits available or commits have not been fetched yet.")
            return
        commit_strings = [f"ID: {entry['commit']}, Message: {entry['subject']}" for entry in self.commits]
        commit_strings.insert(0, "Select a commit")

        self.commit_dropdown_widget = widgets.Dropdown(
            options=commit_strings,
            value=commit_strings[0],
            description='Select:',
            disabled=False,
            layout=Layout(width='auto')
        )

        self.commit_output_area = Output()

        def update_variables(change):
            selected_value = change['new']
            selected_index = commit_strings.index(selected_value)
            selected_index = selected_index - 1

            if selected_index >= 0:
                selected_commit = self.commits[selected_index]
                self.commit_id = selected_commit['commit']

                with self.commit_output_area:
                    self.commit_output_area.clear_output()
                    print(f"Selected commit ID: {self.commit_id}")
                    print(f"Selected commit message: {selected_commit['subject']}")
            else:
                with self.commit_output_area:
                    self.commit_output_area.clear_output()

        self.commit_dropdown_widget.observe(update_variables, names='value')

        display(VBox([self.commit_dropdown_widget, self.commit_output_area]))
        
    def download(self):
        """
        Builds a widget for downloading different types of data.
        """
        data_download_checkboxes = widgets.RadioButtons(
            options=['data_synth', 'models', 'report', 'config', 'metadata'],
            description='Data to Download:',
            disabled=False,
        )

        download_button = widgets.Button(description='Download')

        output_area = Output()

        def on_download_button_click(_):
            selected_data = data_download_checkboxes.value
            with output_area:
                output_area.clear_output()
                try:
                    self.download_data(selected_data)
                    print("Download successful!")  # Success message
                except Exception as e:
                    print(f"An error occurred: {e}")  # Error message

        download_button.on_click(on_download_button_click)

        download_widget = VBox([data_download_checkboxes, download_button, output_area])
        return download_widget
