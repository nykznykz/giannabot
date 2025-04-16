from langchain.tools import BaseTool
from typing import Optional, Dict, Any
import json
import os

class ContactTool(BaseTool):
    name = "contact_lookup"
    description = """A tool for managing contact information. Available operations:
                    1. Add contact: Input should be a JSON string with:
                       operation: "add",
                       name: "contact name",
                       email: "contact email"
                    2. Get contact: Input should be a JSON string with:
                       operation: "get",
                       name: "contact name"
                    3. List contacts: Input should be a JSON string with:
                       operation: "list" """
    
    data_dir = "data"
    contacts_file = os.path.join(data_dir, "contacts.json")
    contacts: Dict[str, str] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        self._load_contacts()
        # Initialize with example contacts if file doesn't exist
        if not os.path.exists(self.contacts_file):
            self._initialize_example_contacts()

    def _initialize_example_contacts(self):
        """Initialize with some example contacts."""
        self.contacts = {
            "laura": "laura@example.com",
            "john": "john.doe@example.com",
            "sarah": "sarah.smith@example.com"
        }
        self._save_contacts()

    def _load_contacts(self):
        """Load contacts from file if it exists."""
        if os.path.exists(self.contacts_file):
            with open(self.contacts_file, 'r') as f:
                self.contacts = json.load(f)

    def _save_contacts(self):
        """Save contacts to file."""
        with open(self.contacts_file, 'w') as f:
            json.dump(self.contacts, f, indent=2)

    def _add_contact(self, data: dict) -> str:
        """Add a new contact."""
        try:
            name = data.get("name")
            email = data.get("email")
            
            if not name or not email:
                return "Error: Both name and email are required for adding a contact"
            
            self.contacts[name.lower()] = email
            self._save_contacts()
            return f"Contact added: {name} ({email})"
        except Exception as e:
            return f"Error adding contact: {str(e)}"

    def _get_contact(self, data: dict) -> str:
        """Get contact information."""
        try:
            name = data.get("name")
            if not name:
                return "Error: Name is required for getting contact information"
            
            email = self.contacts.get(name.lower())
            if not email:
                return f"Error: No contact found with name '{name}'"
            
            return json.dumps({"name": name, "email": email})
        except Exception as e:
            return f"Error getting contact: {str(e)}"

    def _list_contacts(self) -> str:
        """List all contacts."""
        try:
            if not self.contacts:
                return "No contacts found"
            return json.dumps(self.contacts, indent=2)
        except Exception as e:
            return f"Error listing contacts: {str(e)}"

    def _run(self, input_str: str) -> str:
        """Handle contact operations based on input."""
        try:
            # Clean the input string by removing any wrapping quotes
            input_str = input_str.strip().strip("'").strip('"')
            
            # Parse input JSON
            data = json.loads(input_str)
            
            # Get operation type
            operation = data.get("operation")
            if not operation:
                return "Error: Operation type not specified. Please include 'operation' field with value 'add', 'get', or 'list'"
            
            # Handle operation based on type
            if operation == "add":
                return self._add_contact(data)
            elif operation == "get":
                return self._get_contact(data)
            elif operation == "list":
                return self._list_contacts()
            else:
                return f"Error: Invalid operation '{operation}'. Must be one of: add, get, list"
                
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON format. Please ensure the input is valid JSON. Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, query: str) -> str:
        """Async version of _run."""
        return self._run(query) 