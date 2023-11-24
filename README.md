    ## Usage Guide for Syntheticus API

    ### Version 1: Using Widgets (Interactive Approach)

    #### Initialization:
    1. Import and Initialize:
       ```python
       from syntheticus_connect import syntheticus_interact
       client = syntheticus_interact(host_django="your_django_url", host_airflow="your_airflow_url")
       ```

    #### User Authentication:
    2. Login:
       - Execute `client.login_user()`.
       - Input your username and password in the widgets.
       - Click the "Login" button.

    #### Project and Dataset Selection:
    3. Select a Project:
       - Execute `client.project_select()`.
       - Use the dropdown to choose a project.
       - The selected project's details are displayed.
    4. Select a Dataset:
       - Execute `client.dataset_select()`.
       - Use the dropdown to choose a dataset.
       - The selected dataset's details are displayed.

    #### Additional Operations:
    5. Model and Commit Selection, Data Download:
       - Model Selection: Use `client.model_select()` and choose a model from the dropdown.
       - Commit Selection: Use `client.commit_select()` and select a commit from the dropdown.
       - Download Data: Use `client.download()` to download data based on your needs.

    #### Workflow Summary:
    - Start by initializing and logging in.
    - Select projects and datasets using dropdown menus.
    - Perform additional operations (model selection, commit selection, data download) as needed.
    - Refresh widgets after changing selections to update the interface.

    ---

    ### Version 2: Using Command-Line Interface (Non-Interactive Approach)

    #### Initialization:
    1. Import and Initialize:
       ```python
       from syntheticus_connect import syntheticus_client
       client = syntheticus_client(host_django="your_django_url", host_airflow="your_airflow_url")
       ```

    #### User Authentication:
    2. Login:
       - Execute `client.login("your_username", "your_password")`.

    #### Project and Dataset Selection:
    3. List and Select a Project:
       - Use `client.list_projects()` to view available projects.
       - Manually select a project by executing `client.select_project(project_id)`.
    4. List and Select a Dataset:
       - Use `client.list_datasets()` to view available datasets.
       - Manually select a dataset by executing `client.select_dataset(dataset_id)`.

    #### Additional Operations:
    5. Model and Commit Selection, Data Download:
       - List and Select a Model: Use `client.list_models()` and manually select a model by `client.select_model(model_id)`.
       - List and Select a Commit: Use `client.list_commits()` and manually select a commit by `client.select_commit(commit_id)`.
       - Download Data: Use `client.download_data(data_type)` to specify the type of data to download.

    #### Workflow Summary:
    - Initialize and login using command-line commands.
    - List and select projects and datasets manually using the provided methods.
    - Perform additional operations (model and commit selection, data download) using command-line inputs.
    - Update selections manually by re-running the appropriate selection commands.
