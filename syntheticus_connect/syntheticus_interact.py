from ipywidgets import widgets, Layout, VBox, Output
from IPython.display import display
from syntheticus_connect import syntheticus_client
from contextlib import contextmanager

class syntheticus_interface(syntheticus_client):
    def __init__(self, host):
        super().__init__(host)  # Call the constructor of syntheticus_client
    
    @contextmanager
    def suppress_output(self):
        with Output():
            yield
    
    def login_user(self, _):
        # Login widgets
        self.login_username_input = widgets.Text(placeholder="Username")
        self.login_password_input = widgets.Password(placeholder="Password")
        self.login_button = widgets.Button(description="Login")
        self.login_output = Output()  # Create an Output widget
        
        def on_login_button_click(_):
            response = self.login(self.login_username_input.value, self.login_password_input.value)
            with self.login_output:
                print(response)
        
        self.login_button.on_click(on_login_button_click)
        
    def user_login(self):
        self.login_user(None)  # Initialize the login widgets
        display(self.login_username_input, self.login_password_input, self.login_button, self.login_output)
    
    def project_select(self):
        with self.suppress_output():
            self.get_projects()

        project_strings = []
        for project in self.projects_data:
            project_string = f"ID: {project['id']}, Name: {project['name']}"
            project_strings.append(project_string)

        # Create a Dropdown widget with adjusted width using CSS styling
        self.project_dropdown_widget = widgets.Dropdown(
            options=project_strings,
            value=project_strings[0],  # Set the default value to the first project string
            description='Select:',
            disabled=False,
            layout=Layout(width='auto')  # Adjust width automatically
        )

        # Output area to display selected project info
        self.project_output_area = Output()

        # Define a function to update the variables based on the selected dropdown value
        def update_variables(change):
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

        # Display the Dropdown widget and the output area
        display(VBox([self.project_dropdown_widget, self.project_output_area]))

    def dataset_select(self):
        with self.suppress_output():
            self.get_datasets()

        transformed_table_data = []
        for dataset in self.table_data:
            transformed_table_data.append({
                'dataset_name': dataset[0],
                'dataset_id': dataset[1],
                'project_id': dataset[2],
                'data_type': dataset[3],
                'size': dataset[4],
                'rows_number': dataset[5],
                'num_columns': dataset[6],
                'status': dataset[7]
            })
        
        dataset_strings = [f"ID: {entry['dataset_id']}, Name: {entry['dataset_name']}" for entry in transformed_table_data]
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
            selected_index = dataset_strings.index(selected_value)
            selected_index = selected_index - 1

            if selected_index >= 0:
                selected_dataset = transformed_table_data[selected_index]
                self.dataset_id = selected_dataset['dataset_id']
                self.dataset_name = selected_dataset['dataset_name']

                with self.dataset_output_area:
                    self.dataset_output_area.clear_output()
                    print(f"Selected dataset ID: {self.dataset_id}")
                    print(f"Selected dataset Name: {self.dataset_name}")
                    print(f"Project ID: {selected_dataset['project_id']}")
                    print(f"Data Type: {selected_dataset['data_type']}")
                    print(f"Size: {selected_dataset['size']}")
                    print(f"Number of Rows: {selected_dataset['rows_number']}")
                    print(f"Number of Columns: {selected_dataset['num_columns']}")
                    print("\n")
            else:
                with self.dataset_output_area:
                    self.dataset_output_area.clear_output()

        self.dataset_dropdown_widget.observe(update_variables, names='value')

        display(VBox([self.dataset_dropdown_widget, self.dataset_output_area]))

    def model_select(self):
        with self.suppress_output():
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