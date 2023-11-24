from ipywidgets import widgets, Layout, Button, Text, Password, VBox, Output, Dropdown
from IPython.display import display

from syntheticus_connect import syntheticus_client
from contextlib import contextmanager

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
            selected_index = project_strings.index(selected_value)
            selected_project = self.projects_data[selected_index]
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

        # Display the Dropdown widget and the output area only once
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
                self.commit = selected_commit['commit']

                with self.commit_output_area:
                    self.commit_output_area.clear_output()
                    print(f"Selected commit ID: {self.commit}")
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
