import os
from datetime import datetime
from pathlib import Path
import requests
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListView,
    ListItem,
    Static,
    TabbedContent,
    TabPane,
    DataTable,
)
from textual.message import Message
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"

class APIClient:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.username = None

    def set_auth(self, token, user_id, username):
        self.token = token
        self.user_id = user_id
        self.username = username

    def get_headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(self, username, email, password):
        try:
            response = requests.post(f"{BASE_URL}/auth/signup", json={
                "username": username,
                "email": email,
                "password": password
            })
            return response
        except requests.exceptions.RequestException as e:
            return None

    def login(self, email, password):
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            return response
        except requests.exceptions.RequestException as e:
            return None

    def list_files(self):
        try:
            response = requests.get(
                f"{BASE_URL}/file/", 
                headers=self.get_headers(),
                params={"owner_id": self.user_id, "limit": 100}
            )
            return response
        except requests.exceptions.RequestException as e:
            return None

    def upload_file(self, file_path):
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                # owner_id as query param, as per FastAPI default for int
                response = requests.post(
                    f"{BASE_URL}/file/upload",
                    headers=self.get_headers(),
                    files=files,
                    params={"owner_id": self.user_id}
                )
            return response
        except Exception as e:
            return None

    def delete_file(self, file_id):
        try:
            response = requests.delete(
                f"{BASE_URL}/file/{file_id}",
                headers=self.get_headers(),
                params={"owner_id": self.user_id}
            )
            return response
        except requests.exceptions.RequestException as e:
            return None

    def download_file(self, file_id, filename):
        try:
            response = requests.get(
                f"{BASE_URL}/file/download/{file_id}",
                headers=self.get_headers(),
                params={"owner_id": self.user_id},
                stream=True
            )
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            return response
        except Exception as e:
            return None
            

api = APIClient()


class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Container(
            Label("File Upload Service", id="title"),
            Input(placeholder="Email", id="email"),
            Input(placeholder="Password", password=True, id="password"),
            Button("Login", variant="primary", id="login-btn"),
            Button("Go to Register", variant="default", id="goto-register-btn"),
            Label("", id="error-msg", classes="error"),
            id="login-container"
        )

    @on(Button.Pressed, "#login-btn")
    def on_login(self):
        email = self.query_one("#email").value
        password = self.query_one("#password").value
        
        if not email or not password:
            self.query_one("#error-msg").update("Please fill in fields")
            return

        res = api.login(email, password)
        if res and res.status_code == 200:
            data = res.json()
            # login returns: user_id, message, token, token_type
            # assuming username is not returned in login based on code snippet but user_id is.
            username = data.get("username", email) # Fallback if not provided
            api.set_auth(data.get("token"), data.get("user_id"), username)
            self.app.push_screen(MainScreen())
        else:
            msg = "Login failed"
            if res:
                try:
                    detail = res.json().get("detail")
                    if detail:
                        msg = f"Login failed: {detail}"
                except:
                    pass
            self.query_one("#error-msg").update(msg)

    @on(Button.Pressed, "#goto-register-btn")
    def on_register(self):
        self.app.push_screen(RegisterScreen())


class RegisterScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Container(
            Label("Register New User", id="title"),
            Input(placeholder="Username", id="reg-username"),
            Input(placeholder="Email", id="reg-email"),
            Input(placeholder="Password", password=True, id="reg-password"),
            Button("Sign Up", variant="primary", id="signup-btn"),
            Button("Back to Login", variant="default", id="back-btn"),
            Label("", id="reg-error-msg", classes="error"),
            id="register-container"
        )

    @on(Button.Pressed, "#back-btn")
    def on_back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#signup-btn")
    def on_signup(self):
        username = self.query_one("#reg-username").value
        email = self.query_one("#reg-email").value
        password = self.query_one("#reg-password").value
        
        if not username or not email or not password:
            self.query_one("#reg-error-msg").update("Please fill in all fields")
            return

        res = api.register(username, email, password)
        if res and res.status_code == 200:
            data = res.json()
            api.set_auth(data.get("token"), data.get("id"), data.get("username"))
            self.app.push_screen(MainScreen())
        else:
            msg = "Registration failed"
            if res:
                try:
                    detail = res.json().get("detail")
                    if detail:
                        msg = detail
                except:
                    pass
            self.query_one("#reg-error-msg").update(msg)

class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Files"):
                yield Container(
                    Horizontal(
                        Input(placeholder="Enter file path to upload", id="file-path-input", classes="file-input"),
                        Button("Upload", id="upload-btn", variant="success"),
                        classes="action-row"
                    ),
                    Label("", id="upload-status"),
                    DataTable(id="files-table"),
                    Horizontal(
                        Button("Refresh", id="refresh-btn"),
                        Button("Download", id="download-btn", variant="primary"),
                        Button("Delete Selected", id="delete-btn", variant="error"),
                        classes="action-row"
                    )
                )
            with TabPane("Analytics"):
                yield Container(
                   Label("Analytics Feature coming soon", id="analytics-msg")
                )
        yield Footer()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("ID", "Filename", "Type", "Size (bytes)", "Date")
        table.cursor_type = "row"
        self.refresh_files()

    @work(exclusive=True)
    async def refresh_files(self):
        table = self.query_one(DataTable)
        table.clear()
        res = api.list_files()
        if res and res.status_code == 200:
            files = res.json()
            # Sort files by id desc (newest first)
            files.sort(key=lambda x: x['id'], reverse=True)
            for f in files:
                table.add_row(
                    str(f['id']),
                    f.get('uploaded_name', f.get('name', 'Unknown')),
                    f['content_type'],
                    str(f['size']),
                    f['uploaded_at']
                )

    @work(exclusive=True)
    async def upload_file(self):
        path_input = self.query_one("#file-path-input")
        path = path_input.value
        status_lbl = self.query_one("#upload-status")
        
        if not path or not os.path.exists(path):
            status_lbl.update(f"File not found: {path} (PWD: {os.getcwd()})")
            return

        status_lbl.update("Uploading...")
        res = api.upload_file(path)
        if res and res.status_code == 200:
            status_lbl.update("Upload successful!")
            path_input.value = ""
            self.refresh_files()
        else:
            msg = "Upload failed"
            if res:
                try:
                    msg = f"Upload failed: {res.json().get('detail')}"
                except:
                    pass
            status_lbl.update(msg)

    @on(Button.Pressed, "#upload-btn")
    def on_upload_btn(self):
        self.upload_file()

    @on(Button.Pressed, "#refresh-btn")
    def on_refresh_btn(self):
        self.refresh_files()

    @on(Button.Pressed, "#download-btn")
    def on_download_btn(self):
        table = self.query_one(DataTable)
        if table.cursor_row is None:
            self.notify("No file selected")
            return
            
        row_values = table.get_row_at(table.cursor_row)
        file_id = row_values[0]
        filename = row_values[1]
        self.download_file_action(file_id, filename)

    @work(exclusive=True)
    async def download_file_action(self, file_id, filename):
        save_path = f"downloaded_{filename}"
        self.notify(f"Downloading {filename}...")
        res = api.download_file(file_id, save_path)
        if res and res.status_code == 200:
            self.notify(f"Saved to {os.path.abspath(save_path)}")
        else:
            self.notify("Download failed")

    @on(Button.Pressed, "#delete-btn")
    def on_delete_btn(self):
        table = self.query_one(DataTable)
        if table.cursor_row is None:
            return
            
        row_values = table.get_row_at(table.cursor_row)
        file_id = row_values[0]
        self.delete_file_action(file_id)

    @work(exclusive=True)
    async def delete_file_action(self, file_id):
        res = api.delete_file(file_id)
        # 204 or 200 depending on implementation
        if res and (res.status_code == 204 or res.status_code == 200):
            self.notify(f"File {file_id} deleted")
            self.refresh_files()
        else:
            self.notify("Failed to delete file")

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        # Optional: handle row selection
        pass

class FileUploadApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    
    #login-container, #register-container {
        width: 60;
        height: auto;
        border: solid green;
        padding: 1 2;
        box-sizing: border-box; 
    }

    Input {
        margin: 1 0;
    }

    Button {
        width: 100%;
        margin: 1 0;
    }

    .error {
        color: red;
        text-align: center;
    }
    
    .action-row {
        height: auto;
        margin: 1 0;
        align: left middle;
    }
    
    .file-input {
        width: 3fr;
    }
    
    #upload-btn {
        width: 1fr;
    }

    DataTable {
        height: 1fr;
        border: solid white;
    }
    """

    def on_mount(self):
        self.push_screen(LoginScreen())

if __name__ == "__main__":
    app = FileUploadApp()
    app.run()
